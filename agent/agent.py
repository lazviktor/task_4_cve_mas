#!/usr/bin/env python3
import os, sys, platform, subprocess, json, time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import requests, yaml

OSV_QUERYBATCH = "https://api.osv.dev/v1/querybatch"


def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out, err


def detect_os_family() -> str:
    if os.path.exists("/etc/debian_version"):
        return "debian"
    if os.path.exists("/etc/redhat-release") or os.path.exists("/etc/centos-release"):
        return "redhat"
    return "unknown"


def get_dpkg_packages() -> List[Dict[str, str]]:
    code, out, err = run_cmd(["dpkg-query", "-W", "-f=${Package} ${Version}\n"])
    pkgs = []
    if code == 0:
        for line in out.strip().splitlines():
            if not line.strip():
                continue
            name, ver = line.split(" ", 1)
            pkgs.append({"name": name, "version": ver})
    return pkgs


def get_rpm_packages() -> List[Dict[str, str]]:
    code, out, err = run_cmd(["rpm", "-qa", "--qf", "%{NAME} %{EPOCH}:%{VERSION}-%{RELEASE}\n"])
    pkgs = []
    if code == 0:
        for line in out.strip().splitlines():
            if not line.strip():
                continue
            name, ver = line.split(" ", 1)
            ver = ver.replace("(none):", "")
            pkgs.append({"name": name, "version": ver})
    return pkgs


def get_pip_packages() -> List[Dict[str, str]]:
    code, out, err = run_cmd([sys.executable, "-m", "pip", "list", "--format=json"])
    if code != 0:
        return []
    try:
        data = json.loads(out)
    except Exception:
        return []
    return [{"name": i["name"], "version": i["version"]} for i in data]


def build_osv_queries(os_family: str, os_pkgs, pip_pkgs) -> Dict[str, Any]:
    queries = []
    eco = "Debian" if os_family == "debian" else None
    if eco:
        for p in os_pkgs:
            queries.append({"package": {"name": p["name"], "ecosystem": eco}, "version": p["version"]})
    for p in pip_pkgs:
        queries.append({"package": {"name": p["name"], "ecosystem": "PyPI"}, "version": p["version"]})
    return {"queries": queries}


def query_osv_batch(payload: Dict[str, Any]):
    if not payload["queries"]:
        return []
    r = requests.post(OSV_QUERYBATCH, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return [res.get("vulns", []) for res in data.get("results", [])]


def map_results(os_family, os_pkgs, pip_pkgs, results):
    combined = []
    i = 0
    if os_family == "debian":
        for p in os_pkgs:
            combined.append(("os", p, results[i] if i < len(results) else []))
            i += 1
    for p in pip_pkgs:
        combined.append(("pip", p, results[i] if i < len(results) else []))
        i += 1
    return combined


def cvss_to_label(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    if score > 0.0:
        return "LOW"
    return "UNKNOWN"


def pick_severity(v: dict) -> str:
    scores = []
    for s in v.get("severity", []) or []:
        sc = s.get("score")
        if sc is None:
            continue
        try:
            scores.append(float(sc))
        except Exception:
            continue
    return cvss_to_label(max(scores)) if scores else "UNKNOWN"


def pick_cve_id(v: dict) -> str:
    for a in v.get("aliases", []) or []:
        if isinstance(a, str) and a.startswith("CVE-"):
            return a
    return v.get("id", "UNKNOWN")


def flatten_vulnerabilities(mapped) -> List[Dict[str, Any]]:
    vulns: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for kind, pkg, vulns_raw in mapped:
        for v in vulns_raw:
            cve = pick_cve_id(v)
            sev = pick_severity(v)
            vulns.append({
                "cve": cve,
                "severity": sev,
                "found_at": now_iso
            })
    return vulns


def format_vulns_for_db(vulns: list) -> str:
    if not vulns:
        return "[]"
    lines = []
    for v in vulns:
        lines.append(f"- {v['cve']} ({v['severity']}, {v['found_at']})")
    return "\n".join(lines)


def post_report(server_url: str, token: str, payload: Dict[str, Any]):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = server_url.rstrip("/") + "/api/v1/reports"
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        r.raise_for_status()
    except Exception:
        raise RuntimeError(f"POST {url} failed: {r.status_code} {r.text}") from None
    return r.json()


def run_once(cfg: Dict[str, Any]):
    hostname = platform.node()
    os_family = detect_os_family()
    os_pkgs = get_dpkg_packages() if os_family == "debian" else (get_rpm_packages() if os_family == "redhat" else [])
    pip_pkgs = get_pip_packages()

    payload = build_osv_queries(os_family, os_pkgs, pip_pkgs)
    results = query_osv_batch(payload)
    mapped = map_results(os_family, os_pkgs, pip_pkgs, results)
    vulnerabilities = flatten_vulnerabilities(mapped)

    agent_payload = {
        "hostname": hostname,
        "vulnerabilities": format_vulns_for_db(vulnerabilities)
    }

    out_path = os.path.join(os.path.dirname(__file__), "cve_report.json")
    with open(out_path, "w") as f:
        json.dump(agent_payload, f, indent=2, ensure_ascii=False)

    try:
        resp = post_report(
            cfg.get("server_url", "http://127.0.0.1:8000"),
            cfg.get("agent_token", ""),
            agent_payload
        )
        print("[REPORT] Отчёт сохранён в Manager:", resp)
    except Exception as e:
        print("[ERROR] Отправка отчёта провалилась:", e)

    print(f"[{hostname}] vulnerabilities found: {len(vulnerabilities)}")
    print("Saved local report to:", out_path)


def main():
    cfg_path = os.environ.get("AGENT_CONFIG", os.path.join(os.path.dirname(__file__), "config.yaml"))
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f) or {}
    interval = int(cfg.get("interval_minutes", 1))  # по умолчанию 1 минута
    if "--loop" in sys.argv:
        while True:
            try:
                run_once(cfg)
            except Exception as e:
                print("Agent error:", e)
            time.sleep(interval * 60)
    else:
        run_once(cfg)


if __name__ == "__main__":
    main()

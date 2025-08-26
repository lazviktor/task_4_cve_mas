#!/usr/bin/env python3
import os, sys, platform, subprocess, json, time
from datetime import datetime
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
    eco = "Debian" if os_family == "debian" else ("RPM" if os_family == "redhat" else None)
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
    if os_family in ("debian", "redhat"):
        for p in os_pkgs:
            combined.append(("os", p, results[i] if i < len(results) else [])); i += 1
    for p in pip_pkgs:
        combined.append(("pip", p, results[i] if i < len(results) else [])); i += 1
    return combined

def choose_vulnerable(mapped):
    out = {"os": [], "pip": []}
    for kind, pkg, vulns in mapped:
        if not vulns:
            continue
        out[kind].append({
            "name": pkg["name"],
            "version": pkg["version"],
            "cve_ids": [v.get("id") for v in vulns if v.get("id")],
            "summaries": [v.get("summary") for v in vulns if v.get("summary")]
        })
    return out

def os_upgrade_debian(pkgs):
    logs = []
    for cmd in (["apt-get", "update"],
                ["apt-get", "-y", "install", "--only-upgrade"] + pkgs if pkgs else ["apt-get", "-y", "upgrade"]):
        code, out, err = run_cmd(cmd)
        logs.append(f"$ {' '.join(cmd)}\n{out}\n{err}")
        if code != 0:
            break
    return "\n".join(logs)

def os_upgrade_redhat(pkgs):
    logs = []
    cmd = ["yum", "-y", "update"] + (pkgs if pkgs else [])
    code, out, err = run_cmd(cmd)
    logs.append(f"$ {' '.join(cmd)}\n{out}\n{err}")
    return "\n".join(logs)

def pip_upgrade(pkgs):
    logs = []
    for cmd in ([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                [sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs if pkgs else None):
        if cmd is None:
            continue
        code, out, err = run_cmd(cmd)
        logs.append(f"$ {' '.join(cmd)}\n{out}\n{err}")
    return "\n".join(logs)

def patch_vulns(os_family: str, report: Dict[str, Any], scope: str):
    logs = {}
    if scope in ("os", "all"):
        names = sorted({e["name"] for e in report.get("os", [])})
        logs["os"] = os_upgrade_debian(names) if os_family == "debian" else os_upgrade_redhat(names)
    if scope in ("pip", "all"):
        names = sorted({e["name"] for e in report.get("pip", [])})
        logs["pip"] = pip_upgrade(names)
    return logs

def post_report(server_url: str, token: str, payload: Dict[str, Any]):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = server_url.rstrip("/") + "/api/v1/findings"
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def run_once(cfg: Dict[str, Any]):
    hostname = platform.node()
    os_family = detect_os_family()
    os_pkgs = get_dpkg_packages() if os_family == "debian" else (get_rpm_packages() if os_family == "redhat" else [])
    pip_pkgs = get_pip_packages()

    payload = build_osv_queries(os_family, os_pkgs, pip_pkgs)
    results = query_osv_batch(payload)
    mapped = map_results(os_family, os_pkgs, pip_pkgs, results)
    report = choose_vulnerable(mapped)

    agent_payload = {
        "hostname": hostname,
        "os_family": os_family,
        "found_at": datetime.utcnow().isoformat() + "Z",
        "report": report,
        "autopatch_enabled": bool(cfg.get("auto_patch", False)),
    }

    if cfg.get("auto_patch", False) and (report.get("os") or report.get("pip")):
        agent_payload["patch_log"] = patch_vulns(os_family, report, cfg.get("patch_scope", "os"))

    out_path = os.path.join(os.path.dirname(__file__), "cve_report.json")
    with open(out_path, "w") as f:
        json.dump(agent_payload, f, indent=2, ensure_ascii=False)

    try:
        resp = post_report(cfg.get("server_url", "http://127.0.0.1:8000"), cfg.get("agent_token", ""), agent_payload)
        print("Report posted:", resp)
    except Exception as e:
        print("Post failed:", e)

    total = len(report.get("os", [])) + len(report.get("pip", []))
    print(f"[{hostname}] vulnerabilities found: {total}")
    print("Saved local report to:", out_path)

def main():
    cfg_path = os.environ.get("AGENT_CONFIG", os.path.join(os.path.dirname(__file__), "config.yaml"))
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)
    if "--loop" in sys.argv:
        interval = int(cfg.get("interval_minutes", 60))
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

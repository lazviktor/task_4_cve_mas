
#!/usr/bin/env python3
import argparse, socket, requests, yaml

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manager", required=True, help="http://MANAGER_HOST:8000")
    p.add_argument("--config", required=True, help="path to agent/config.yaml")
    args = p.parse_args()
    hostname = socket.gethostname()
    url = args.manager.rstrip("/") + "/api/v1/agents/register"
    r = requests.post(url, json={"hostname": hostname}, timeout=30)
    r.raise_for_status()
    token = r.json()["token"]
    print("Received token:", token)
    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)
    cfg["agent_token"] = token
    with open(args.config, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
    print("Config updated:", args.config)

if __name__ == "__main__":
    main()

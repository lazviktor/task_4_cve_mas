#!/usr/bin/env bash
# Install Task 4 agent as systemd service (Ubuntu/Debian)
# Usage:
#   sudo bash agent_install.sh http://MANAGER_HOST:8000 <TOKEN or empty>
set -e
if [ -z "$1" ]; then
  echo "Usage: sudo bash agent_install.sh <MANAGER_URL> <TOKEN or empty>"
  exit 1
fi
MANAGER_URL="$1"
TOKEN="${2:-}"
BASE="/opt/mas_template/task_4/agent"
sudo apt-get update
sudo apt-get install -y python3 python3-pip
sudo mkdir -p "$BASE"
sudo cp -r ../agent/* "$BASE"/
sudo sed -i "s|server_url:.*|server_url: \"$MANAGER_URL\"|g" "$BASE/config.yaml"
if [ -n "$TOKEN" ]; then
  sudo sed -i "s|agent_token:.*|agent_token: \"$TOKEN\"|g" "$BASE/config.yaml"
fi
sudo cp "$BASE/vuln-agent.service" /etc/systemd/system/mas-task4-agent.service
sudo systemctl daemon-reload
sudo systemctl enable mas-task4-agent.service
sudo systemctl start mas-task4-agent.service
echo "Agent installed and started."

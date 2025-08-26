    #!/usr/bin/env bash
    # Install Task 4 manager as systemd service (Ubuntu/Debian)
    set -e
    BASE="/opt/mas_template/task_4/manager"
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip
    sudo mkdir -p "$BASE"
    sudo cp -r ../manager/* "$BASE"/
    cd "$BASE"
    python3 -m venv .venv
    . .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cat <<SERVICE | sudo tee /etc/systemd/system/mas-task4-manager.service
    [Unit]
    Description=MAS Task 4 Manager (FastAPI)
    After=network.target

    [Service]
    Type=simple
    WorkingDirectory=$BASE
    Environment=DATABASE_URL=sqlite:///$BASE/data.db
    ExecStart=$BASE/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
SERVICE
    sudo systemctl daemon-reload
    sudo systemctl enable mas-task4-manager.service
    sudo systemctl start mas-task4-manager.service
    echo "Manager running on port 8000"

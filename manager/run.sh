#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./data.db"
uvicorn app.main:app --host 0.0.0.0 --port 8000

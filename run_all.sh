#!/bin/bash
set -e

MANAGER_URL="http://127.0.0.1:8000"

echo "[INFO] Запрашиваем новый токен GigaChat..."
TOKEN=$(curl -s -k -X POST "https://ngw.devices.sberbank.ru:9443/api/v2/oauth" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  -H "RqUID: $(uuidgen)" \
  -H "Authorization: Basic NDQ0YWM1MjAtNWJiZi00ZDkzLWEyOTktNjQyNzFiNmM4ZWQyOmUzMjI1OWNkLTc2OGItNDNhNi04OGIxLTgzZTI4Nzk4YzliYg==" \
  --data-urlencode 'scope=GIGACHAT_API_PERS' \
  --data-urlencode 'grant_type=client_credentials' \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token',''))")

if [[ -z "$TOKEN" ]]; then
  echo "[ERROR] Не удалось получить токен"
  exit 1
fi

echo "export GIGACHAT_API_KEY=\"$TOKEN\"" > ~/.gigachat.env
source ~/.gigachat.env
echo "[OK] Токен сохранён и подключён"

cd ~/Desktop/task_4_cve_mas

echo "[INFO] Запускаем Agent..."
python3 agent/agent.py &
AGENT_PID=$!

sleep 5

echo "[INFO] Запускаем LLM-анализатор..."
cd llm_agent
python3 analyzer.py &
LLM_PID=$!

cd ..
echo "[SUCCESS] Система запущена!"
echo "Agent PID=$AGENT_PID, LLM PID=$LLM_PID"
echo "Чтобы остановить: kill -9 $AGENT_PID $LLM_PID"


#!/bin/bash

echo "[INFO] Останавливаем старые процессы..."
pkill -9 -f "uvicorn" || true
pkill -9 -f "agent.py" || true
pkill -9 -f "analyzer.py" || true

echo "[INFO] Устанавливаем зависимости..."
cd ~/Desktop/task_4_cve_mas || exit 1
python3 -m pip install -r manager/requirements.txt > /dev/null 2>&1 || true

echo "[INFO] Запускаем Manager..."
cd ~/Desktop/task_4_cve_mas/manager || exit 1
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 > ../manager.log 2>&1 &
MANAGER_PID=$!

echo "[INFO] Ждём запуска Manager на http://127.0.0.1:8000 ..."
for i in {1..20}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/docs || echo 000)
    if [ "$STATUS" == "200" ]; then
        echo "[SUCCESS] Manager запущен (PID=$MANAGER_PID)"
        break
    else
        echo "[WAIT] Попытка $i... (код=$STATUS)"
        sleep 2
    fi
done

if [ "$STATUS" != "200" ]; then
    echo "[ERROR] Manager не удалось запустить!"
    exit 1
fi

echo "[INFO] Запускаем Agent..."
cd ~/Desktop/task_4_cve_mas
source ~/.gigachat.env
nohup python3 agent/agent.py > agent.log 2>&1 &
AGENT_PID=$!

sleep 5

echo "[INFO] Запускаем LLM-анализ..."
cd ~/Desktop/task_4_cve_mas/llm_agent
nohup python3 analyzer.py --manager http://127.0.0.1:8000 > analyzer.log 2>&1 &
LLM_PID=$!

cd ~/Desktop/task_4_cve_mas

echo "[SUCCESS] Система запущена!"
echo "  - Manager PID: $MANAGER_PID (http://127.0.0.1:8000)"
echo "  - Agent   PID: $AGENT_PID"
echo "  - LLM PID: $LLM_PID"
echo
echo "Открой http://127.0.0.1:8000 в браузере → MAS Dashboard"
echo "Логи: manager.log, agent.log, analyzer.log"

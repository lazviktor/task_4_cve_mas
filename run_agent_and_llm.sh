#!/bin/bash
set -e

echo "[INFO] Загружаем токен GigaChat..."
if [ -z "$GIGACHAT_API_KEY" ]; then
    if [ -f ~/.gigachat.env ]; then
        source ~/.gigachat.env
    fi
fi

if [ -z "$GIGACHAT_API_KEY" ]; then
    echo "[ERROR] Не найден токен GigaChat. Выполни: echo 'export GIGACHAT_API_KEY=\"ТВОЙ_ТОКЕН\"' > ~/.gigachat.env && source ~/.gigachat.env"
    exit 1
fi
echo "[INFO] Токен найден (длина: ${#GIGACHAT_API_KEY})"

cd ~/Desktop/task_4_cve_mas

echo "[INFO] Запускаем Agent..."
python3 agent/agent.py &
AGENT_PID=$!

sleep 5

echo "[INFO] Запускаем LLM-анализ..."
python3 llm_agent/analyzer.py --manager http://127.0.0.1:8000 --output llm_agent/analysis.txt || echo "[WARN] Анализатор не смог получить данные"

echo "[INFO] Отчёт сохранён: llm_agent/analysis.txt"
echo "[INFO] Agent работает в фоне (PID=$AGENT_PID). Чтобы остановить: kill -9 $AGENT_PID"

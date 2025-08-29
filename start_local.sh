#!/bin/bash
set -e

MANAGER_URL="http://127.0.0.1:8000"
AUTH_KEY="NDQ0YWM1MjAtNWJiZi00ZDkzLWEyOTktNjQyNzFiNmM4ZWQyOmVmOGE2OGJjLTRkYjYtNDgwZi04ZmQ5LTYwNGM5OGJlMGI4OA=="

echo "[INFO] Устанавливаем зависимости..."
pip3 install -r manager/requirements.txt -q
pip3 install -r agent/requirements.txt -q
pip3 install -r llm_agent/requirements.txt -q

echo "[INFO] Запускаем Manager в фоне..."
cd manager
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > ../manager.log 2>&1 &
MANAGER_PID=$!
cd ..

echo "[INFO] Ждём пока Manager поднимется..."
for i in {1..20}; do
  if curl -s http://127.0.0.1:8000/docs > /dev/null; then
    echo "[SUCCESS] Manager доступен на $MANAGER_URL"
    break
  fi
  echo "[WAIT] Попытка $i..."
  sleep 2
done

echo "[INFO] Регистрируем агент..."
python3 deploy/register_agent.py --manager $MANAGER_URL --config agent/config.yaml || {
  echo "[ERROR] Не удалось зарегистрировать агент"; kill $MANAGER_PID; exit 1;
}

echo "[INFO] Проверяем config.yaml..."
cat agent/config.yaml

echo "[INFO] Запускаем Agent..."
cd agent
nohup python3 agent.py > ../agent.log 2>&1 &
AGENT_PID=$!
cd ..

echo "[INFO] Получаем токен GigaChat..."
cd llm_agent
./get_token.sh "$AUTH_KEY" || { echo "[ERROR] Не удалось получить токен"; kill $MANAGER_PID; kill $AGENT_PID; exit 1; }
source ~/.gigachat.env
echo "[SUCCESS] Токен получен"

echo "[INFO] Запускаем LLM-анализ..."
nohup python3 analyzer.py --manager $MANAGER_URL --output analysis.txt > ../analyzer.log 2>&1 &
cd ..

echo "[INFO] Всё запущено!"
echo "------------------------------------"
echo "🌍 Дашборд: $MANAGER_URL"
echo "📜 Swagger API: $MANAGER_URL/docs"
echo "📝 Отчёты: http://127.0.0.1:8000/api/v1/reports"
echo "📑 LLM-анализ: ./llm_agent/analysis.txt"
echo "📂 Логи: tail -f manager.log | agent/agent.log | analyzer.log"
echo "------------------------------------"

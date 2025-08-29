#!/bin/bash
set -e

MANAGER_URL="http://127.0.0.1:8000"

echo "[TEST] 1. Создаём новый отчёт..."
REPORT=$(curl -s -X POST $MANAGER_URL/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{"hostname":"MacBook-Pro-victor","vulnerabilities":"[]"}')

echo "Ответ: $REPORT"

REPORT_ID=$(echo $REPORT | jq -r '.id')
echo "[INFO] Report ID = $REPORT_ID"

echo "[TEST] 2. Добавляем анализ в отчёт $REPORT_ID..."
ANALYSIS=$(curl -s -X POST $MANAGER_URL/api/v1/reports/$REPORT_ID/analysis \
  -H "Content-Type: application/json" \
  -d '{"analysis":"Это результат анализа от GigaChat"}')

echo "Ответ: $ANALYSIS"

echo "[TEST] 3. Получаем список всех отчётов..."
curl -s $MANAGER_URL/api/v1/reports | jq

echo "[SUCCESS] Проверка завершена ✅"

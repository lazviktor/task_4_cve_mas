#!/bin/bash
set -e

AUTH_KEY="$1"

if [ -z "$AUTH_KEY" ]; then
  echo "[ERROR] Укажите Base64 Authorization_key как аргумент:"
  echo "Пример: ./get_token.sh NDQ0YWM1...=="
  exit 1
fi

echo "[INFO] Запрашиваем access_token у GigaChat API..."

RESPONSE=$(curl -sk -X POST "https://ngw.devices.sberbank.ru:9443/api/v2/oauth" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  -H "Authorization: Basic $AUTH_KEY" \
  -d "scope=GIGACHAT_API_PERS")

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token',''))" || true)

if [ -z "$TOKEN" ]; then
  echo "[ERROR] Не удалось получить токен!"
  echo "Ответ сервера: $RESPONSE"
  exit 1
fi

printf 'export GIGACHAT_API_KEY=%q\n' "$TOKEN" > ~/.gigachat.env

echo "[SUCCESS] Токен получен и сохранён в ~/.gigachat.env"
echo "[INFO] Для активации токена в текущей сессии выполните:"
echo "source ~/.gigachat.env"

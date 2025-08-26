#!/usr/bin/env bash
# Получение токена GigaChat вручную
# Использование: ./get_token.sh <Authorization_key>

if [ -z "$1" ]; then
  echo "Укажите Authorization_key (base64 строка)"
  exit 1
fi

AUTH_KEY="$1"

TOKEN=$(curl -s -L -X POST 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'      -H "Content-Type: application/x-www-form-urlencoded"      -H "Accept: application/json"      -H "RqUID: $(uuidgen)"      -H "Authorization: Basic $AUTH_KEY"      --data-urlencode 'scope=GIGACHAT_API_PERS' | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  export GIGACHAT_API_KEY="$TOKEN"
  echo "export GIGACHAT_API_KEY=$TOKEN" > ~/.gigachat.env
  echo "[INFO] Токен сохранён в ~/.gigachat.env и доступен в окружении"
else
  echo "[ERROR] Не удалось получить токен"
fi

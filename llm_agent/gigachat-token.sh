#!/usr/bin/env bash
# Автообновление токена GigaChat каждые 25 минут
AUTH_KEY="ВСТАВЬ_СЮДА_СВОЙ_Authorization_key"

while true; do
  RESPONSE=$(curl -s -L -X POST 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'        -H "Content-Type: application/x-www-form-urlencoded"        -H "Accept: application/json"        -H "RqUID: $(uuidgen)"        -H "Authorization: Basic $AUTH_KEY"        --data-urlencode 'scope=GIGACHAT_API_PERS')

  TOKEN=$(echo $RESPONSE | jq -r '.access_token')

  if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "export GIGACHAT_API_KEY=$TOKEN" > /etc/profile.d/gigachat.sh
    echo "[INFO] Новый токен установлен в /etc/profile.d/gigachat.sh"
  else
    echo "[ERROR] Ошибка получения токена: $RESPONSE"
  fi

  sleep 1500  # 25 минут
done

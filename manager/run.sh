#!/bin/bash
set -e

# Запускаем Uvicorn из корня проекта, чтобы работали относительные импорты
cd "$(dirname "$0")/.."

exec uvicorn manager.app:app --host 0.0.0.0 --port 8000 --reload


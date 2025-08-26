# Task 4 — CVE Vulnerability Management (MAS + GigaChat LLM)

Состав:
- `agent/` — сканер уязвимостей (dpkg/rpm + pip + OSV.dev) и опциональный патчер.
- `manager/` — FastAPI сервер: приём отчётов, хранение, дашборд, хранение LLM‑аналитики.
- `llm_agent/` — агент‑аналитик на GigaChat: превращает JSON в человеко‑читаемый отчёт и может отправлять его в менеджер.
- `deploy/` — скрипты установки менеджера/агента как systemd‑сервисов и регистрации агента.

## Быстрый старт (локально)
1) Запустить менеджер:
```bash
cd manager
bash run.sh
# Откройте http://127.0.0.1:8000
```

2) Зарегистрировать агента и прописать токен:
```bash
python3 deploy/register_agent.py --manager http://127.0.0.1:8000 --config agent/config.yaml
```

3) Запустить сканер (разово):
```bash
cd agent
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
sudo python3 agent.py
```

4) Запустить LLM‑агента (GigaChat):
```bash
cd llm_agent
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
export GIGACHAT_API_KEY="ВАШ_ТОКЕН"
# вариант А: из локального JSON
python3 analyzer.py --report ../agent/cve_report.json --output analysis.txt
# вариант Б: взять последний отчёт с менеджера и сохранить анализ обратно
python3 analyzer.py --manager http://127.0.0.1:8000 --output analysis.txt
```

## Сервисы
- Менеджер (FastAPI): `http://<IP>:8000/` — дашборд; `/api/v1/reports/{id}` — JSON+analysis.
- Агент (systemd): `mas-task4-agent.service` (опционально).

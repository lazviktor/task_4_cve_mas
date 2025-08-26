# 🛡️ Task 4 — CVE Vulnerability Management (MAS + GigaChat LLM)

## 📖 Описание
Проект реализует **мультиагентную систему (MAS)** для выявления и устранения CVE-уязвимостей в ПО.  
Агенты выполняют сканирование окружения (OS-пакеты, Python-зависимости), сверку с базой **[OSV.dev](https://osv.dev/)**,  
автоматическое устранение уязвимостей и передачу отчётов на центральный **Manager-сервер**.  

LLM-агент на основе **GigaChat** анализирует JSON-отчёты и формирует человеко-читаемые рекомендации для инженеров по безопасности.  

---

## 🏗️ Архитектура
```
┌──────────────┐      ┌───────────────┐
│   Agent      │ ---> │    Manager    │ ---> Dashboard + API
│ (Scanner+Patch)     │ (FastAPI)     │
└──────────────┘      └───────────────┘
        │                        │
        ▼                        ▼
   cve_report.json         JSON Reports DB
                                │
                                ▼
                        ┌──────────────┐
                        │  LLM Agent   │ (GigaChat)
                        │ (analyzer.py)│
                        └──────────────┘
```

- **Agent**: собирает список пакетов (dpkg/rpm + pip), сверяет с OSV.dev, формирует отчёт, может запускать обновления.  
- **Manager (FastAPI)**: принимает отчёты, хранит их в SQLite, предоставляет REST API и дашборд.  
- **LLM Agent (GigaChat)**: анализирует отчёты, выделяет CVE, генерирует краткий отчёт, может сохранять его в Manager.  

---

## 🚀 Быстрый старт (локально)

### 1. Manager
```bash
cd manager
bash run.sh
# Открой http://127.0.0.1:8000
```

### 2. Agent
```bash
python3 deploy/register_agent.py --manager http://127.0.0.1:8000 --config agent/config.yaml
cd agent
pip install -r requirements.txt
sudo python3 agent.py
```

### 3. LLM Agent (GigaChat)
```bash
cd llm_agent
pip install -r requirements.txt
export GIGACHAT_API_KEY="ВАШ_ТОКЕН"
python3 analyzer.py --manager http://127.0.0.1:8000 --output analysis.txt
```

---

## ⚡ One-liner Demo
```bash
cd ~/task_4/manager && bash run.sh &
cd ~/task_4 && sudo python3 deploy/register_agent.py --manager http://127.0.0.1:8000 --config agent/config.yaml
cd ~/task_4/agent && sudo python3 agent.py
cd ~/task_4/llm_agent && ./get_token.sh <Authorization_key> && source ~/.gigachat.env
python3 analyzer.py --manager http://127.0.0.1:8000 --output analysis.txt
```

---

## 🔑 Работа с токеном GigaChat

### Ручной способ
```bash
cd llm_agent
./get_token.sh <Authorization_key>
source ~/.gigachat.env
```

### Автоматический (systemd)
```bash
sudo cp llm_agent/gigachat-token.sh /opt/mas_template/task_4/llm_agent/
sudo cp llm_agent/gigachat-token.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gigachat-token.service
sudo systemctl start gigachat-token.service
```

---

## 📊 Пример дашборда
После запуска Manager доступен дашборд по адресу:  
👉 `http://127.0.0.1:8000`  

Там видно:
- список отчётов,
- количество уязвимостей (OS/PyPI),
- отметка о наличии LLM-анализа.  

---

## 🧩 Стек
- Python 3.10+  
- FastAPI, SQLAlchemy, Jinja2  
- requests, PyYAML  
- GigaChat API (LLM)  
- OSV.dev API  

---

## 👨‍💻 Авторы
Команда **lazviktor** (Hackathon 2025)  

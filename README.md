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

установить : 
  pip3 install requests
  sudo apt install python3-yaml
  pip3 install argparse
  pip3 install gigachat
  pip3 install uvicorn
  pip3 install fastapi

  шаг 1:  cd task_4_cve_mas/
  шаг 2 запускаем менеджера: python3 -m uvicorn manager.app:app --host 0.0.0.0 --port 8000
  шаг 3 запускаем LLM: ./run_with_llm.sh
  открываем дашборд : 10.62.28.10
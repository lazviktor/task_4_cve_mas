import time
import os
import requests
from gigachat import GigaChat

MANAGER_URL = "http://127.0.0.1:8000"

# Загружаем токен из переменной окружения
TOKEN = os.getenv("GIGACHAT_TOKEN")   # поменял переменную на GIGACHAT_TOKEN

if not TOKEN:
    print("[ERROR] Нет токена. Выполни: source ~/.gigachat.env")
    exit(1)


def get_reports():
    try:
        r = requests.get(f"{MANAGER_URL}/api/v1/reports", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERROR] Не удалось получить отчёты: {e}")
        return []


def analyze_report(report: dict):
    question = f"Анализируй отчёт:\nHost: {report['hostname']}\nVulnerabilities: {report['vulnerabilities']}"
    # ✅ теперь используем access_token, а не credentials
    with GigaChat(access_token=TOKEN, verify_ssl_certs=False) as giga:
        response = giga.chat(question)
        return response.choices[0].message.content


def save_analysis(report_id: int, analysis: str):
    try:
        r = requests.post(
            f"{MANAGER_URL}/api/v1/reports/{report_id}/analysis",
            json={"analysis": analysis},
            timeout=10,
        )
        r.raise_for_status()
        print(f"[SUCCESS] LLM-анализ добавлен в отчёт {report_id}")
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить анализ для отчёта {report_id}: {e}")


def main():
    print("[LLM] Анализатор запущен, работает в цикле...")
    while True:
        reports = get_reports()
        for r in reports:
            if not r.get("analysis"):  # только новые
                try:
                    analysis = analyze_report(r)
                    save_analysis(r["id"], analysis)
                except Exception as e:
                    print(f"[ERROR] Ошибка при анализе: {e}")
        time.sleep(15)


if __name__ == "__main__":
    main()

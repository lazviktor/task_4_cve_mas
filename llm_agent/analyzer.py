#!/usr/bin/env python3
import os, json, argparse, requests

try:
    from gigachat import GigaChat
except Exception as e:
    raise SystemExit("Не установлен пакет gigachat: pip install gigachat") from e

def read_report(path):
    with open(path, "r") as f:
        return json.load(f)

def fetch_latest_report(manager_url: str):
    r = requests.get(manager_url.rstrip("/") + "/api/v1/reports", timeout=30)
    r.raise_for_status()
    lst = r.json()
    if not lst:
        raise RuntimeError("Нет отчётов на менеджере")
    rid = lst[0]["id"]
    r2 = requests.get(manager_url.rstrip("/") + f"/api/v1/reports/{rid}", timeout=30)
    r2.raise_for_status()
    return rid, r2.json()

def upload_analysis(manager_url: str, report_id: int, text: str):
    body = {"report_id": report_id, "text": text}
    r = requests.post(manager_url.rstrip("/") + "/api/v1/analysis", json=body, timeout=30)
    r.raise_for_status()
    return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api_key", default=os.environ.get("GIGACHAT_API_KEY"))
    p.add_argument("--report", default=None, help="Путь до agent/cve_report.json (если не указано, берём с менеджера)")
    p.add_argument("--manager", default=None, help="URL менеджера (например, http://127.0.0.1:8000)")
    p.add_argument("--output", default="analysis.txt")
    args = p.parse_args()

    if not args.api_key:
        raise SystemExit("Не найден API ключ GigaChat. Установите GIGACHAT_API_KEY")

    report_id = None
    data = None
    if args.report:
        data = read_report(args.report)
    elif args.manager:
        report_id, payload = fetch_latest_report(args.manager)
        data = payload["json"]
    else:
        raise SystemExit("Укажите --report или --manager")

    client = GigaChat(credentials=args.api_key, scope="GIGACHAT_API_PERS")

    prompt = f"""
    Вот JSON-отчёт об уязвимостях сервера:
    {json.dumps(data, ensure_ascii=False, indent=2)}

    Сформируй краткий отчёт для инженера безопасности:
    - ТОП-5 уязвимых пакетов с указанием CVE и краткого объяснения риска.
    - Привяжи уязвимости к сервисам (nginx, zabbix, cargo, rsksatte), если это очевидно.
    - Дай приоритеты (P1 критично, P2 важно, P3 средне).
    - Список команд для устранения (apt/yum/pip) в формате чек-листа.
    Ответ должен быть на русском, без воды.
    """

    resp = client.chat.completions.create(
        model="GigaChat:latest",
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.choices[0].message["content"]

    with open(args.output, "w") as f:
        f.write(text)
    print("Аналитический отчёт сохранён в", args.output)

    if args.manager and report_id is not None:
        try:
            upload_analysis(args.manager, report_id, text)
            print("Аналитика сохранена в менеджере (report_id =", report_id, ")")
        except Exception as e:
            print("Не удалось загрузить аналитику в менеджер:", e)

if __name__ == "__main__":
    main()

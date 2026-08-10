import os
import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def inspect_db_via_console():
    print("=== INSPECTING PYTHONANYWHERE DB & CAMPAIGNS ===")
    
    # 1. Get console ID
    r_consoles = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
    consoles = r_consoles.json() if r_consoles.status_code == 200 else []
    
    console_id = None
    if isinstance(consoles, list) and len(consoles) > 0:
        console_id = consoles[0]["id"]
    else:
        r_create = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
        console_id = r_create.json()["id"]

    query_cmd = (
        "python3 -c \""
        "import sqlite3, os; "
        "db_path = '/home/JHFGUF/jobhunt/data/jobhunt_saas.db'; "
        "print('DB Exists:', os.path.exists(db_path)); "
        "conn = sqlite3.connect(db_path); "
        "camps = conn.execute('SELECT campaign_id, user_id, status, target_role, created_at FROM campaigns').fetchall(); "
        "print('=== CAMPAIGNS IN DB ===', len(camps)); "
        "for c in camps[:10]: print(c); "
        "jobs_cnt = conn.execute('SELECT count(*) FROM jobs').fetchone()[0]; "
        "print('Total Scraped Jobs in DB:', jobs_cnt); "
        "users_cnt = conn.execute('SELECT count(*) FROM users').fetchone()[0]; "
        "print('Total Users in DB:', users_cnt); "
        "sent_cnt = conn.execute('SELECT count(*) FROM campaign_emails').fetchone()[0]; "
        "print('Total Emails Sent in DB:', sent_cnt); "
        "\"\n"
    )

    r_send = SESSION.post(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/",
        json={"input": query_cmd}
    )
    import time
    time.sleep(5)

    r_out = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/")
    if r_out.status_code == 200:
        output = r_out.json().get("output", "")
        print("=== Console Output ===")
        print(output[-1200:])
        print("======================")

if __name__ == "__main__":
    inspect_db_via_console()

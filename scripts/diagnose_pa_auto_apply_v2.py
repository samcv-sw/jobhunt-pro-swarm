import os
import sys
import time
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

REMOTE_AUDIT_SCRIPT = """import sqlite3
import os

db_paths = [
    '/home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db',
    '/home/JHFGUF/jobhunt/jobhunt_saas_v2.db',
    '/home/JHFGUF/jobhunt/data/jobhunt_saas.db',
]

report_path = '/home/JHFGUF/jobhunt/data/db_v2_status_report.txt'
lines = []

for db_path in db_paths:
    lines.append(f"=== DB PATH: {db_path} ===")
    lines.append(f"Exists: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        lines.append(f"Size: {os.path.getsize(db_path)} bytes")
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            camps = conn.execute("SELECT campaign_id, status, target_role, created_at FROM campaigns ORDER BY id DESC LIMIT 10").fetchall()
            lines.append(f"Campaigns count in {os.path.basename(db_path)}: {len(camps)}")
            for c in camps:
                lines.append(f"  - {c['campaign_id']} | Status: {c['status']} | Role: {c['target_role']} | Created: {c['created_at']}")
            
            sent_emails = conn.execute("SELECT count(*) as cnt FROM campaign_emails").fetchone()["cnt"]
            lines.append(f"Sent emails count: {sent_emails}")

            conn.close()
        except Exception as e:
            lines.append(f"Error: {e}")
    lines.append("")

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\\n".join(lines))
"""

def diagnose_v2():
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/scripts/remote_db_audit_v2.py"
    SESSION.post(upload_url, files={"content": REMOTE_AUDIT_SCRIPT.encode('utf-8')})

    r_consoles = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
    consoles = r_consoles.json() if r_consoles.status_code == 200 else []
    console_id = consoles[0]["id"] if isinstance(consoles, list) and len(consoles) > 0 else None
    if not console_id:
        r_create = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
        console_id = r_create.json()["id"]

    cmd = "python3 /home/JHFGUF/jobhunt/scripts/remote_db_audit_v2.py\n"
    SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/", json={"input": cmd})
    time.sleep(4)

    report_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/data/db_v2_status_report.txt"
    r_report = SESSION.get(report_url)
    if r_report.status_code == 200:
        print("\n=======================================================")
        print(r_report.text)
        print("=======================================================")
    else:
        print(f"[!] Report status HTTP {r_report.status_code}")

if __name__ == "__main__":
    diagnose_v2()

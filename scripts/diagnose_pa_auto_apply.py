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

# 1. Python audit script to run on PythonAnywhere
REMOTE_AUDIT_SCRIPT = """import sqlite3
import os
import sys
from datetime import datetime

db_path = '/home/JHFGUF/jobhunt/data/jobhunt_saas.db'
report_path = '/home/JHFGUF/jobhunt/data/db_status_report.txt'

lines = []
lines.append("=== PYTHONANYWHERE AUTO-APPLY DIAGNOSTIC REPORT ===")
lines.append(f"Report Generated At: {datetime.now().isoformat()}")
lines.append(f"DB Path Exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Check campaigns
        camps = conn.execute("SELECT campaign_id, user_id, status, target_role, created_at FROM campaigns ORDER BY id DESC LIMIT 20").fetchall()
        lines.append(f"Total Campaigns Found: {len(camps)}")
        for c in camps:
            lines.append(f"  - Campaign {c['campaign_id']} | User: {c['user_id']} | Status: {c['status']} | Role: {c['target_role']} | Created: {c['created_at']}")

        # Check pending/active campaigns
        active_camps = conn.execute("SELECT campaign_id, status FROM campaigns WHERE status IN ('active', 'running', 'pending')").fetchall()
        lines.append(f"Active/Pending Campaigns Count: {len(active_camps)}")

        # Check jobs count
        jobs_count = conn.execute("SELECT count(*) as cnt FROM jobs").fetchone()["cnt"]
        lines.append(f"Scraped Jobs in DB: {jobs_count}")

        # Check users count
        users = conn.execute("SELECT user_id, email, tokens, wallet_balance FROM users LIMIT 10").fetchall()
        lines.append(f"Users Count: {len(users)}")
        for u in users:
            lines.append(f"  - User {u['user_id']} ({u['email']}) | Tokens: {u['tokens']} | Wallet: ${u['wallet_balance']}")

        # Check sent emails count
        sent_emails = conn.execute("SELECT count(*) as cnt FROM campaign_emails").fetchone()["cnt"]
        lines.append(f"Total Sent Emails Recorded: {sent_emails}")

        # Check recent 5 sent emails
        recent_sent = conn.execute("SELECT campaign_id, company_name, job_title, status, sent_at FROM campaign_emails ORDER BY id DESC LIMIT 5").fetchall()
        lines.append(f"Recent Sent Emails:")
        for r in recent_sent:
            lines.append(f"  - {r['company_name']} ({r['job_title']}) -> Status: {r['status']} | SentAt: {r['sent_at']}")

        conn.close()
    except Exception as e:
        lines.append(f"Error querying DB: {e}")

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\\n".join(lines))

print("Report saved successfully.")
"""

def run_diagnostics():
    print("=== RUNNING REMOTE DB & AUTO-APPLY DIAGNOSTICS ===")

    # 1. Upload remote audit script to PA
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/scripts/remote_db_audit.py"
    r_up = SESSION.post(upload_url, files={"content": REMOTE_AUDIT_SCRIPT.encode('utf-8')})
    print(f"[*] Uploaded remote_db_audit.py (HTTP {r_up.status_code})")

    # 2. Execute via bash console
    r_consoles = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
    consoles = r_consoles.json() if r_consoles.status_code == 200 else []
    console_id = consoles[0]["id"] if isinstance(consoles, list) and len(consoles) > 0 else None

    if not console_id:
        r_create = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
        console_id = r_create.json()["id"]

    cmd = "python3 /home/JHFGUF/jobhunt/scripts/remote_db_audit.py\n"
    SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/", json={"input": cmd})
    
    print("[*] Diagnostic command sent to console. Waiting 4 seconds...")
    time.sleep(4)

    # 3. Read report file
    report_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/data/db_status_report.txt"
    r_report = SESSION.get(report_url)
    if r_report.status_code == 200:
        print("\n=======================================================")
        print(r_report.text)
        print("=======================================================")
    else:
        print(f"[!] Failed to read report file: HTTP {r_report.status_code}")

if __name__ == "__main__":
    run_diagnostics()

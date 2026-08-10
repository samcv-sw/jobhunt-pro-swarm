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
DOMAIN = "jhfguf.pythonanywhere.com"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def upload_db():
    local_db = os.path.join(PROJECT_ROOT, "data", "jobhunt_saas_v2.db")
    if not os.path.exists(local_db):
        print(f"[!] Local DB not found at {local_db}")
        return False

    size_mb = os.path.getsize(local_db) / (1024 * 1024)
    print(f"[*] Local DB size: {size_mb:.2f} MB")
    print("[*] Uploading local jobhunt_saas_v2.db to PythonAnywhere /home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db...")

    remote_path = f"/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db"
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"

    with open(local_db, "rb") as f:
        r_up = SESSION.post(upload_url, files={"content": f}, timeout=180)

    if r_up.status_code in (200, 201):
        print(f"[✓ SUCCESS] Database uploaded to PythonAnywhere (HTTP {r_up.status_code})")
    else:
        print(f"[!] Upload failed with HTTP {r_up.status_code}: {r_up.text}")
        return False

    # Also upload to root directory /home/JHFGUF/jobhunt/jobhunt_saas_v2.db just in case!
    remote_path_root = f"/home/{USERNAME}/jobhunt/jobhunt_saas_v2.db"
    upload_url_root = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path_root}"
    with open(local_db, "rb") as f:
        SESSION.post(upload_url_root, files={"content": f}, timeout=180)
    print(f"[✓ SUCCESS] Database copy placed in root /home/JHFGUF/jobhunt/jobhunt_saas_v2.db")

    # Reload WebApp to restart daemon with fresh DB
    print("[*] Reloading WebApp on PythonAnywhere...")
    r_reload = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] WebApp Reload Status: {r_reload.status_code}")
    return True

if __name__ == "__main__":
    upload_db()

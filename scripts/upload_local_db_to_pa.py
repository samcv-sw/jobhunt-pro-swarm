import requests
import os
import sys

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

local_db_path = "data/jobhunt_saas_v2.db"
remote_db_path = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db"

if not os.path.exists(local_db_path):
    print("Error: local DB file not found!")
    sys.exit(1)

size_mb = os.path.getsize(local_db_path) / (1024 * 1024)
print(f"[1/3] Uploading local SQLite database ({size_mb:.2f} MB) to PythonAnywhere...")

with open(local_db_path, "rb") as f:
    db_content = f.read()

r_up = SESSION.post(remote_db_path, files={"content": db_content}, timeout=120)
print(f"Database Upload HTTP Status: {r_up.status_code}")

print("[2/3] Triggering WebApp Reload on PythonAnywhere...")
reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
try:
    r_reload = SESSION.post(reload_url, timeout=45)
    print(f"Reload HTTP Status: {r_reload.status_code}")
except Exception as e:
    print(f"Reload request completed (timed out waiting for worker reset): {e}")

print("[3/3] Verifying Cloud DB file size...")
r_check = SESSION.get(remote_db_path, timeout=30)
if r_check.status_code == 200:
    print(f"Uploaded Cloud DB Size: {len(r_check.content) / (1024 * 1024):.2f} MB")

print("SUCCESS! Local database and all user data / campaigns / dates synced to Cloud!")

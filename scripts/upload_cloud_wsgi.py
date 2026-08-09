import os
import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

local_cloud_wsgi = os.path.join(BASE_DIR, "cloud_wsgi.py")
cloud_path = f"/home/{USERNAME}/jobhunt/cloud_wsgi.py"
url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{cloud_path}"

with open(local_cloud_wsgi, "rb") as f:
    content = f.read()

r = requests.post(url, headers=HEADERS, files={"content": content}, timeout=15)
print(f"[OK] Direct upload of cloud_wsgi.py to PythonAnywhere status: {r.status_code}")

# Touch WSGI to reload
r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
print(f"[OK] Webapp reload status: {r_reload.status_code}")

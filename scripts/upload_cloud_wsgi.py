import os
import sys
import time
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

uploaded = False
for attempt in range(5):
    try:
        r = requests.post(url, headers=HEADERS, files={"content": content}, timeout=15)
        print(f"[Attempt {attempt+1}] Direct upload of cloud_wsgi.py status: {r.status_code}")
        if r.status_code in (200, 201):
            uploaded = True
            break
        elif r.status_code == 429:
            print("[429 Rate Limit] Sleeping 5s before retry...")
            time.sleep(5)
    except Exception as e:
        print(f"Exception: {e}")
        time.sleep(3)

if uploaded:
    time.sleep(3)
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"[OK] Webapp reload status: {r_reload.status_code}")

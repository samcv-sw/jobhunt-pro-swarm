import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

log_files = [
    f"/var/log/{USERNAME.lower()}.pythonanywhere.com.error.log",
    f"/var/log/{USERNAME.lower()}.pythonanywhere.com.server.log",
]

for log_path in log_files:
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{log_path}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 200:
        print(f"=== {log_path} (Last 3000 chars) ===")
        print(r.text[-3000:])
        print("==========================================")
    else:
        print(f"Failed to fetch {log_path}: {r.status_code}")

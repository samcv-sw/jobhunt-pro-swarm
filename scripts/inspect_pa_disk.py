import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

# List files in home directory
url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/"
r = requests.get(url, headers=HEADERS, timeout=15)
if r.status_code == 200:
    data = r.json()
    print(f"=== Directory listing /home/{USERNAME}/ ===")
    for item, info in data.items():
        print(f"  {item} -> type: {info.get('type')}, size: {info.get('size', 'N/A')}")
else:
    print(f"Failed: {r.status_code}")

"""Direct PA file upload - hotmail pool + app_v2.py"""
import requests, time
PA_TOKEN = "1181b0064725fc1bb9f3043c19f943780eeebd3b"
BASE = "https://www.pythonanywhere.com/api/v0/user/jhfguf/"
H = {"Authorization": f"Token {PA_TOKEN}"}

files = [
    ("core/hotmail_pool.py", r"C:\Users\samde\Desktop\cv sam new ma3 kimi\core\hotmail_pool.py"),
    ("web/app_v2.py", r"C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py"),
    ("data/hotmail_pool.json", r"C:\Users\samde\Desktop\cv sam new ma3 kimi\data\hotmail_pool.json"),
]

for remote, local in files:
    url = f"{BASE}files/path/home/JHFGUF/jobhunt/{remote}"
    with open(local, 'rb') as f:
        r = requests.post(url, headers=H, files={'content': f})
    if r.status_code in (200, 201):
        print(f"OK {remote}")
    else:
        print(f"FAIL {remote}: {r.status_code}")

r = requests.post(f"{BASE}webapps/jhfguf.pythonanywhere.com/reload/", headers=H)
print(f"Reload: {r.status_code} {r.text[:100]}")

time.sleep(5)
r = requests.get("https://jhfguf.pythonanywhere.com/api/hotmail/stats", timeout=15)
print(f"Hotmail endpoint: {r.status_code} {r.text[:300]}")

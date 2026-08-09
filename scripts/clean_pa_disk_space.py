import requests
import time

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

consoles_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
r = SESSION.get(consoles_url)
console_id = None
if r.status_code == 200:
    for c in r.json():
        if c.get("executable") == "bash":
            console_id = c.get("id")
            break

if not console_id:
    r_new = SESSION.post(consoles_url, json={"executable": "bash"})
    console_id = r_new.json().get("id")

print(f"Executing disk cleanup on Console #{console_id}...")

cleanup_cmd = (
    "rm -f /home/JHFGUF/*.zip /home/JHFGUF/*.tar /home/JHFGUF/*.gz /home/JHFGUF/deploy_bundle.zip; "
    "rm -rf /home/JHFGUF/.cache/pip /home/JHFGUF/.cache/wheel; "
    "rm -rf /home/JHFGUF/jobhunt/.git/objects/pack/* 2>/dev/null; "
    "rm -rf /home/JHFGUF/jobhunt/mobile /home/JHFGUF/jobhunt/frontend /home/JHFGUF/jobhunt/test_env 2>/dev/null; "
    "df -h /home/JHFGUF > /home/JHFGUF/quota.txt\n"
)

SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/", json={"input": cleanup_cmd})
time.sleep(10)

r_quota = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/quota.txt")
print("=== PYTHONANYWHERE DISK SPACE FREED ===")
print(r_quota.text)

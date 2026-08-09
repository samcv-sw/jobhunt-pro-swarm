import requests
import time

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

print("1. Fetching bash consoles...")
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

print(f"Using console #{console_id}")
cmd = "du -h --max-depth=2 /home/JHFGUF > /home/JHFGUF/disk_usage.txt\n"
SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/", json={"input": cmd})
time.sleep(8)

r_file = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/disk_usage.txt")
print("=== DISK USAGE ON PYTHONANYWHERE ===")
print(r_file.text[:3000])

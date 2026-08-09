import os
import sys
import time
import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

def force_git_pull_on_pa():
    print("=== Force Git Pull & Reload on PythonAnywhere via Consoles API ===")
    
    # 1. Get existing consoles or create a new bash console
    r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", headers=HEADERS)
    consoles = r.json() if r.status_code == 200 else []
    
    console_id = None
    if isinstance(consoles, list) and len(consoles) > 0:
        console_id = consoles[0]["id"]
        print(f"[*] Found existing console ID: {console_id}")
    else:
        print("[*] Creating new bash console...")
        r_create = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", headers=HEADERS, json={"executable": "bash"})
        if r_create.status_code in (200, 201):
            console_id = r_create.json()["id"]
            print(f"[✓] Created console ID: {console_id}")
        else:
            print(f"[!] Failed to create console: {r_create.text}")
            return False

    # 2. Send commands to fetch main, reset --hard, and reload webapp
    cmd = (
        "cd /home/JHFGUF/jobhunt && "
        "git fetch origin main && "
        "git reset --hard origin/main && "
        "touch /var/www/jhfguf_pythonanywhere_com_wsgi.py\n"
    )
    print(f"[*] Sending git pull command to console {console_id}...")
    r_send = requests.post(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/",
        headers=HEADERS,
        json={"input": cmd}
    )
    print(f"[*] Send input status: {r_send.status_code}")
    
    time.sleep(5)
    
    # 3. Read output log from console
    r_out = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/", headers=HEADERS)
    if r_out.status_code == 200:
        output = r_out.json().get("output", "")
        print("=== Console Output ===")
        print(output[-1000:])
        print("======================")

    # 4. Trigger webapp reload
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/jhfguf.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"[✓] Webapp reload status: {r_reload.status_code}")
    return True

if __name__ == "__main__":
    force_git_pull_on_pa()

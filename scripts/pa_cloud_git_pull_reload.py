import requests
import time
import sys

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"

HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def run_git_pull_and_reload():
    print(f"=== [1/4] Checking PythonAnywhere Consoles for {USERNAME} ===")
    consoles_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
    r = SESSION.get(consoles_url, timeout=30)
    print(f"Consoles GET status: {r.status_code}")
    
    console_id = None
    if r.status_code == 200:
        consoles = r.json()
        for c in consoles:
            if c.get("executable") == "bash":
                console_id = c.get("id")
                print(f"Found existing bash console #{console_id}")
                break
                
    if not console_id:
        print("Creating new bash console...")
        r_create = SESSION.post(consoles_url, json={"executable": "bash"}, timeout=30)
        print(f"Create console status: {r_create.status_code}")
        if r_create.status_code in (200, 201):
            console_id = r_create.json().get("id")
            print(f"Created console ID: {console_id}")
            time.sleep(3)

    if console_id:
        print(f"=== [2/4] Sending 'git pull' command to Console #{console_id} ===")
        cmd_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
        git_cmd = "cd /home/JHFGUF/jobhunt 2>/dev/null || cd /home/JHFGUF; git pull origin main\n"
        r_cmd = SESSION.post(cmd_url, json={"input": git_cmd}, timeout=30)
        print(f"Send input status: {r_cmd.status_code}")
        time.sleep(5)
    else:
        print("Warning: Could not obtain bash console. Proceeding to webapp reload.")

    print(f"=== [3/4] Reloading WebApp {DOMAIN} via PA API ===")
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    try:
        r_reload = SESSION.post(reload_url, timeout=45)
        print(f"WebApp Reload API status: {r_reload.status_code}")
    except requests.exceptions.Timeout:
        print("WebApp reload requested (timed out waiting for response, which is normal for PA worker resets).")
    except Exception as e:
        print(f"WebApp reload exception: {e}")

    time.sleep(5)

    print(f"=== [4/4] Verifying Live WebApp Response ===")
    try:
        r_live = requests.get(f"https://{DOMAIN}/health", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print(f"Live /health check: Status {r_live.status_code}")
        if r_live.status_code == 200:
            print("Response:", r_live.text[:200])
    except Exception as e:
        print(f"Live verification check failed: {e}")

    try:
        r_root = requests.get(f"https://{DOMAIN}/login", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print(f"Live /login check: Status {r_root.status_code}")
    except Exception as e:
        print(f"Live login check failed: {e}")

if __name__ == "__main__":
    run_git_pull_and_reload()

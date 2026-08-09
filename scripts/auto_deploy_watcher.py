"""
Autonomous Background Deploy Watcher for PythonAnywhere
"""
import sys
import time
import requests
import re
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

USERNAME = "JHFGUF"
PASSWORD = "JHGjhf5475%^"
DOMAIN = "jhfguf.pythonanywhere.com"
API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"

def attempt_deployment():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    headers_api = {"Authorization": f"Token {API_TOKEN}"}
    
    try:
        r_check = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/", headers=headers_api, timeout=10)
        if r_check.status_code == 503:
            return False, "PythonAnywhere is still in maintenance mode (503)"
        if r_check.status_code != 200:
            return False, f"API check returned status {r_check.status_code}"
    except Exception as e:
        return False, f"Connection error: {e}"

    print("[AUTONOMOUS WATCHER] PythonAnywhere maintenance ended! Executing auto-deployment now...")
    
    try:
        r_ext = session.post(
            f"https://www.pythonanywhere.com/user/{USERNAME}/webapps/{DOMAIN}/extend",
            headers={"Referer": f"https://www.pythonanywhere.com/user/{USERNAME}/webapps/"},
            timeout=15
        )
        print(f"Extend Status: {r_ext.status_code}")

        files_to_sync = [
            ("web/routers/api_v2.py", f"/home/{USERNAME}/jobhunt/web/routers/api_v2.py"),
            ("web/app_v2.py", f"/home/{USERNAME}/jobhunt/web/app_v2.py"),
            ("web/templates/en/dashboard_v3.html", f"/home/{USERNAME}/jobhunt/web/templates/en/dashboard_v3.html"),
        ]
        
        for local_rel, remote_path in files_to_sync:
            if os.path.exists(local_rel):
                with open(local_rel, "rb") as f:
                    content = f.read()
                upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
                r_up = session.post(upload_url, headers=headers_api, files={"content": content}, timeout=20)
                print(f"Uploaded {local_rel} -> {remote_path} (Status: {r_up.status_code})")

        reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
        r_reload = session.post(reload_url, headers=headers_api, timeout=15)
        print(f"API Reload Status: {r_reload.status_code}")

        r_live = session.get(f"https://{DOMAIN}/", timeout=15)
        if r_live.status_code == 200:
            print("[SUCCESS] Deployment verified! Live Cloud App is online 200 OK!")
            return True, "Live site 200 OK"
        else:
            print(f"App reloaded, live HTTP status: {r_live.status_code}")
            return True, f"Live status {r_live.status_code}"

    except Exception as err:
        return False, f"Deployment error: {err}"

def run_watcher():
    print("====================================================================")
    print("   AUTONOMOUS CLOUD DEPLOYMENT WATCHER STARTED")
    print("====================================================================")
    print("Monitoring PythonAnywhere maintenance status...")
    
    attempts = 0
    while True:
        attempts += 1
        success, msg = attempt_deployment()
        if success:
            print(f"[SUCCESS] Auto-deployment successful on attempt {attempts}: {msg}")
            break
        print(f"[{attempts}] Status: {msg}. Retrying in 15 seconds...")
        time.sleep(15)

if __name__ == "__main__":
    run_watcher()

import os
import sys
import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES_TO_UPLOAD = [
    "web/app_v2.py",
    "web/shared.py",
    "web/routers/auth.py",
    "web/routers/auto_applier.py",
    "web/routers/dashboard.py",
    "web/routers/payments.py",
    "web/templates/_dashboard_shell.html",
    "web/templates/en/_dashboard_shell.html",
    "web/templates/en/oauth_prompt.html",
    "web/templates/en/sent_emails.html",
    "web/templates/oauth_prompt.html",
    "web/templates/sent_emails.html",
    "web/templates/zh/oauth_prompt.html",
    "web/templates/zh/sent_emails.html",
    "core/curated_contacts.py",
    "core/email_engine.py",
    "core/job_queue.py",
    "core/lebanon_company_seeder.py",
    "core/continuous_dispatcher.py",
    "web/templates/battle_station.html",
    "web/templates/en/battle_station.html",
    "web/templates/microsoft_login_ui.html",
    "web/templates/en/microsoft_login_ui.html",
    "cloud_wsgi.py"
]

def upload_files():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    print(f"[*] Starting direct upload of {len(FILES_TO_UPLOAD)} files to PythonAnywhere...", flush=True)
    success_count = 0
    
    for rel_path in FILES_TO_UPLOAD:
        local_path = os.path.join(PROJECT_ROOT, rel_path.replace("/", os.sep))
        if not os.path.exists(local_path):
            print(f"[!] File not found: {local_path}", flush=True)
            continue
            
        remote_path = f"/home/{USERNAME}/jobhunt/{rel_path}"
        upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
        
        import time
        time.sleep(1)
        with open(local_path, "rb") as f:
            resp = session.post(upload_url, files={"content": f}, timeout=30)
            
        if resp.status_code in (200, 201):
            print(f"  [OK] Uploaded {rel_path} (HTTP {resp.status_code})", flush=True)
            success_count += 1
        else:
            print(f"  [ERR] Failed to upload {rel_path} (HTTP {resp.status_code}): {resp.text}", flush=True)

    print(f"\n[OK] Successfully uploaded {success_count}/{len(FILES_TO_UPLOAD)} files.", flush=True)
    
    # Reload webapp
    print("[*] Triggering webapp reload on PythonAnywhere...", flush=True)
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    try:
        reload_resp = session.post(reload_url, timeout=60)
        print(f"[OK] Reload status: HTTP {reload_resp.status_code}", flush=True)
    except Exception as re_err:
        print(f"[!] Reload request initial attempt note: {re_err}. Retrying...", flush=True)
        try:
            reload_resp = session.post(reload_url, timeout=60)
            print(f"[OK] Retry reload status: HTTP {reload_resp.status_code}", flush=True)
        except Exception as re_err2:
            print(f"[!] Reload warning: {re_err2}", flush=True)
    
    # Verify live site
    import time
    print("[*] Waiting 8s for PythonAnywhere WSGI workers to spin up...", flush=True)
    time.sleep(8)
    print("[*] Testing live response from https://jhfguf.pythonanywhere.com/ping ...", flush=True)
    try:
        ping_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        r_ping = requests.get(f"https://{DOMAIN}/ping", headers=ping_headers, timeout=20)
        print(f"[OK] Live Ping Response: HTTP {r_ping.status_code} -> {r_ping.text[:100]}", flush=True)
    except Exception as e:
        print(f"[ERR] Ping error: {e}", flush=True)

if __name__ == "__main__":
    upload_files()

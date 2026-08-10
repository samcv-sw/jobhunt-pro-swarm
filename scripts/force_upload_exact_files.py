import os
import sys
import hashlib
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

target_files = [
    "web/templates/upload_cv_v3.html",
    "web/templates/en/upload_cv_v3.html",
    "web/app_v2.py",
    "web/routers/jobs.py",
    "cloud_wsgi.py"
]

def force_upload():
    print("=== FORCE UPLOADING EXACT TARGET FILES ===")
    for rel_path in target_files:
        url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/{rel_path}"
        with open(rel_path, "rb") as f:
            r = SESSION.post(url, files={"content": f}, timeout=30)
        print(f"[Upload] {rel_path} -> HTTP {r.status_code}")

        # Fetch and verify hash
        r_get = SESSION.get(url, timeout=10)
        local_hash = hashlib.md5(open(rel_path, "rb").read()).hexdigest()
        remote_hash = hashlib.md5(r_get.content).hexdigest()
        symbol = "✓ MATCH" if local_hash == remote_hash else "✗ MISMATCH"
        print(f"  [{symbol}] Local: {local_hash} | Remote: {remote_hash}")

    print("\n[*] Triggering WebApp Reload on PythonAnywhere...")
    r_reload = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] Reload Status: {r_reload.status_code}")

if __name__ == "__main__":
    force_upload()

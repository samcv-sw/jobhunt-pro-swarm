import os
import sys
import time
import requests
import hashlib

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
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_DIRS = {".git", ".venv", ".venv2", "node_modules", ".pytest_cache", "__pycache__", "archive", "cache", ".agents", ".gemini", "brain"}
EXCLUDE_EXTS = {".pyc", ".log", ".zip"}

def get_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def force_sync_all():
    print("=== FORCE SYNCING ALL LOCAL FILES DIRECTLY VIA PYTHONANYWHERE FILES API ===")
    file_count = 0
    updated_count = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTS or file.startswith('.'):
                continue
            if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                continue

            abs_file = os.path.join(root, file)
            rel_file = os.path.relpath(abs_file, PROJECT_ROOT).replace("\\", "/")
            remote_path = f"/home/{USERNAME}/jobhunt/{rel_file}"

            with open(abs_file, "rb") as f:
                content = f.read()

            upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
            
            # Check remote MD5 first
            r_get = SESSION.get(upload_url)
            if r_get.status_code == 200 and get_md5(r_get.content) == get_md5(content):
                file_count += 1
                continue

            # Upload / Overwrite file on PA
            r_up = SESSION.post(upload_url, files={"content": content}, timeout=30)
            if r_up.status_code in (200, 201):
                updated_count += 1
                file_count += 1
                if updated_count % 10 == 0 or rel_file in ["web/app_v2.py", "web/templates/upload_cv_v3.html", "cloud_wsgi.py"]:
                    print(f"[✓ Uploaded {updated_count}] {rel_file}")
            else:
                print(f"[! Failed] {rel_file} -> Status {r_up.status_code}")

    print(f"\n[✓ SYNC COMPLETE] Processed {file_count} files, updated {updated_count} outdated files on PythonAnywhere.")

    # Reload WebApp
    print("[*] Reloading WebApp on PythonAnywhere...")
    r_reload = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] Reload Status: {r_reload.status_code}")

if __name__ == "__main__":
    force_sync_all()

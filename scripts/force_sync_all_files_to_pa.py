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

EXCLUDE_DIRS = {
    ".git", ".venv", ".venv2", "test_env", "test_env_2", "data", "logs", "screenshots",
    "node_modules", ".pytest_cache", "__pycache__", "archive", "cache", ".agents", ".gemini", "brain", ".next",
    "frontend", "frontend-vue", "mobile", "extension", "dashboard", "bot", "chat_images", "chrome_extension", "backend-node"
}
EXCLUDE_EXTS = {".pyc", ".log", ".zip", ".tflite", ".webm", ".pack", ".db", ".sqlite", ".sqlite3"}

def get_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def force_sync_all():
    print("=== FORCE SYNCING ALL LOCAL APP FILES DIRECTLY VIA PYTHONANYWHERE FILES API ===")
    file_count = 0
    updated_count = 0

    target_dirs = ["web", "core", "scripts", "backend"]
    target_root_files = ["cloud_wsgi.py", "config.py", "app.py", "main.py", "webhook_bot.py", "requirements.txt", "requirements_optimized.txt"]

    files_to_sync = []
    for td in target_dirs:
        abs_td = os.path.join(PROJECT_ROOT, td)
        if os.path.exists(abs_td):
            for root, dirs, files in os.walk(abs_td):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in EXCLUDE_EXTS or file.startswith('.'):
                        continue
                    files_to_sync.append(os.path.join(root, file))

    for trf in target_root_files:
        abs_trf = os.path.join(PROJECT_ROOT, trf)
        if os.path.exists(abs_trf):
            files_to_sync.append(abs_trf)

    for abs_file in files_to_sync:
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
            print(f"[✓ Uploaded {updated_count}] {rel_file}")
        else:
            print(f"[! Failed] {rel_file} -> Status {r_up.status_code}")

    print(f"\n[✓ SYNC COMPLETE] Processed {file_count} files, updated {updated_count} outdated files on PythonAnywhere.")

    # Reload WebApp
    print("[*] Reloading WebApp on PythonAnywhere...")
    r_reload = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] Reload Status: {r_reload.status_code}")

    time.sleep(4)

    # Health Check
    print("\n=== RUNNING LIVE HTTP HEALTH AUDIT ===")
    test_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    endpoints_to_test = [
        ("/", "Homepage"),
        ("/login", "Login Page"),
        ("/pricing", "Pricing Page"),
        ("/dashboard", "Dashboard"),
        ("/resume-tailor", "Resume Tailor"),
        ("/ats-scorer", "ATS Scorer"),
    ]
    for ep, name in endpoints_to_test:
        url = f"https://{DOMAIN}{ep}"
        try:
            r = requests.get(url, headers=test_headers, timeout=15)
            status_symbol = "✓" if r.status_code in (200, 302) else "✗"
            print(f"[{status_symbol}] {name} ({ep}): HTTP {r.status_code}")
        except Exception as err:
            print(f"[✗] {name} ({ep}): Request Error ({err})")

if __name__ == "__main__":
    force_sync_all()

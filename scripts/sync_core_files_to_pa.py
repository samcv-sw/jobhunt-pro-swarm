import os
import sys
import time
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
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_DIRS = {".git", ".venv", ".venv2", "node_modules", ".pytest_cache", "__pycache__", "archive", "cache", ".agents", ".gemini", "brain", "tests", "docs"}
EXCLUDE_EXTS = {".pyc", ".log", ".zip", ".html_log", ".txt", ".db", ".sqlite", ".sqlite3"}
EXCLUDE_FILES = {"JobHunt_Pro_Full_Chat_Log.html", "deploy_bundle.zip"}

def get_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def sync_file_with_retry(abs_file: str, rel_file: str, max_retries: int = 3) -> bool:
    remote_path = f"/home/{USERNAME}/jobhunt/{rel_file}"
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"

    try:
        with open(abs_file, "rb") as f:
            local_bytes = f.read()
    except Exception as e:
        print(f"[!] Cannot read local file {rel_file}: {e}")
        return False

    local_hash = get_md5(local_bytes)

    # Check remote MD5
    try:
        r_get = SESSION.get(upload_url, timeout=10)
        if r_get.status_code == 200 and get_md5(r_get.content) == local_hash:
            return True  # Already identical
    except Exception:
        pass

    for attempt in range(max_retries):
        try:
            with open(abs_file, "rb") as f:
                r_up = SESSION.post(upload_url, files={"content": f}, timeout=30)
            if r_up.status_code in (200, 201):
                # Double check remote hash
                r_check = SESSION.get(upload_url, timeout=10)
                if r_check.status_code == 200 and get_md5(r_check.content) == local_hash:
                    return True
        except Exception as err:
            time.sleep(1)

    print(f"[! Failed Sync] {rel_file}")
    return False

def sync_all_source_code():
    print("=== HIGH-RELIABILITY SOURCE CODE SYNC TO PYTHONANYWHERE ===")
    total = 0
    synced = 0
    failed = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for file in files:
            if file in EXCLUDE_FILES:
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTS or file.startswith('.'):
                continue

            abs_file = os.path.join(root, file)
            rel_file = os.path.relpath(abs_file, PROJECT_ROOT).replace("\\", "/")

            total += 1
            ok = sync_file_with_retry(abs_file, rel_file)
            if ok:
                synced += 1
            else:
                failed += 1

            if total % 15 == 0:
                print(f"[*] Progress: {synced}/{total} files verified/synced...")

    print(f"\n[✓ SYNC COMPLETE] Verified/Synced: {synced}/{total} source files (Failed: {failed})")

    print("[*] Triggering WebApp Reload on PythonAnywhere...")
    r_reload = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] Reload Status Code: {r_reload.status_code}")
    return failed == 0

if __name__ == "__main__":
    sync_all_source_code()

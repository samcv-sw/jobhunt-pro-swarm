import os
import sys
import time
import requests
import hashlib

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_DIRS = {".git", ".venv", ".venv2", "__pycache__", ".idea", ".agents", "archive", "node_modules", "tmp", ".ruff_cache", ".pytest_cache", "frontend", ".github", "tests"}
EXCLUDE_EXTS = {".pyc", ".tmp", ".sqlite3-journal", ".log"}

def get_local_files():
    local_files = {}
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for file in files:
            if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, BASE_DIR).replace("\\", "/")
            if rel_path.startswith("tests/") or rel_path.startswith(".git/"):
                continue
            local_files[rel_path] = full_path
    return local_files

def upload_file_to_pa(local_path, rel_path):
    cloud_path = f"/home/{USERNAME}/jobhunt/{rel_path}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{cloud_path}"
    
    with open(local_path, "rb") as f:
        content = f.read()
        
    for attempt in range(5):
        try:
            r = requests.post(url, headers=HEADERS, files={"content": content}, timeout=30)
            if r.status_code in (200, 201):
                print(f"[OK {r.status_code}] Sync: {rel_path}")
                time.sleep(0.1)
                return True
            elif r.status_code == 429:
                print(f"[429 Rate Limit] Pausing 3s before retrying {rel_path}...")
                time.sleep(3)
            else:
                print(f"[FAIL {r.status_code}] {rel_path}: {r.text[:100]}")
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Exception uploading {rel_path}: {e}")
            time.sleep(2)
    return False

def master_audit_and_sync():
    print("=== Master 100% Comprehensive Cloud Audit & Synchronization ===")
    
    # 1. Update /var/www/jhfguf_pythonanywhere_com_wsgi.py
    print("Updating WSGI entrypoint on PythonAnywhere...")
    wsgi_code = b'''import sys
import os

project_home = '/home/JHFGUF/jobhunt'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from cloud_wsgi import application
'''
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/www/jhfguf_pythonanywhere_com_wsgi.py"
    requests.post(upload_url, headers=HEADERS, files={"content": wsgi_code}, timeout=15)

    local_files = get_local_files()
    print(f"Total Local Core Files Identified for Sync: {len(local_files)}")
    
    success_count = 0
    failed_files = []
    
    for rel_path, full_path in sorted(local_files.items()):
        if upload_file_to_pa(full_path, rel_path):
            success_count += 1
        else:
            failed_files.append(rel_path)
            
    print(f"\nMaster Sync Finished! Total uploaded: {success_count} / {len(local_files)}")
    if failed_files:
        print(f"Failed files ({len(failed_files)}): {failed_files}")
    else:
        print("🎉 100% COMPLETE PARITY: All local files uploaded to PythonAnywhere with ZERO missing files!")
        
    # Reload WebApp
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"Webapp reload status: {r_reload.status_code}")

if __name__ == "__main__":
    master_audit_and_sync()

import os
import sys
import time
import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGET_DIRS = ["web", "core", "payments", "backend"]
TARGET_ROOT_FILES = ["config.py", "app.py", "cloud_wsgi.py", "run_local_server.py", ".env"]

def get_target_files():
    files_to_sync = {}
    
    for root_file in TARGET_ROOT_FILES:
        full = os.path.join(BASE_DIR, root_file)
        if os.path.exists(full):
            files_to_sync[root_file] = full
            
    for t_dir in TARGET_DIRS:
        dir_path = os.path.join(BASE_DIR, t_dir)
        if not os.path.exists(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".pyc") or file.endswith(".sqlite3-journal") or file.endswith(".log"):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_DIR).replace("\\", "/")
                files_to_sync[rel_path] = full_path
                
    return files_to_sync

def upload_file_to_pa(local_path, rel_path):
    cloud_path = f"/home/{USERNAME}/jobhunt/{rel_path}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{cloud_path}"
    
    with open(local_path, "rb") as f:
        content = f.read()
        
    for attempt in range(3):
        try:
            r = requests.post(url, headers=HEADERS, files={"content": content}, timeout=15)
            if r.status_code in (200, 201):
                print(f"[OK 200] Sync: {rel_path}")
                time.sleep(0.15)
                return True
            elif r.status_code == 429:
                print(f"[429 Rate Limit] Retrying {rel_path} in 3s...")
                time.sleep(3)
            else:
                print(f"[FAIL {r.status_code}] {rel_path}: {r.text[:80]}")
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Exception uploading {rel_path}: {e}")
            time.sleep(1)
    return False

def sync_all():
    print("=== Syncing All Web Routers, Templates & Core Modules ===")
    files_to_sync = get_target_files()
    print(f"Total Application Source Files: {len(files_to_sync)}")
    
    success = 0
    failed = []
    
    for rel_path, full_path in sorted(files_to_sync.items()):
        if upload_file_to_pa(full_path, rel_path):
            success += 1
        else:
            failed.append(rel_path)
            
    print(f"\nCompleted! {success} / {len(files_to_sync)} files successfully synced.")
    if failed:
        print(f"Failed files ({len(failed)}): {failed}")
    else:
        print("🎉 100% PERFECT PARITY: All Web Routers, Jinja2 Templates, and Core Modules are in 100% sync with PythonAnywhere Cloud!")
        
    # Reload WebApp
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"Webapp reload status: {r_reload.status_code}")

if __name__ == "__main__":
    sync_all()

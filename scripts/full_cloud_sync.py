import os
import sys
import time
import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIRS_TO_SYNC = ["web", "core", "backend"]
FILES_TO_SYNC = ["config.py", ".env", "cloud_wsgi.py"]

def upload_file(local_path, rel_path):
    cloud_path = f"/home/{USERNAME}/jobhunt/{rel_path.replace('\\', '/')}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{cloud_path}"
    
    with open(local_path, "rb") as f:
        content = f.read()
        
    for attempt in range(5):
        try:
            r = requests.post(url, headers=HEADERS, files={"content": content}, timeout=10)
            if r.status_code in (200, 201):
                print(f"[OK 200] Uploaded: {rel_path}")
                time.sleep(0.15)
                return True
            elif r.status_code == 429:
                print(f"[429 Rate Limit] Retrying {rel_path} in 2s...")
                time.sleep(2)
            else:
                print(f"[FAIL {r.status_code}] Failed to upload {rel_path}: {r.text[:100]}")
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Exception uploading {rel_path}: {e}")
            time.sleep(2)
    return False

def sync_all():
    print("Starting 100% Guaranteed Robust Project Cloud Sync to PythonAnywhere...")
    total_uploaded = 0
    failed_files = []
    
    for f in FILES_TO_SYNC:
        local_p = os.path.join(BASE_DIR, f)
        if os.path.exists(local_p):
            if upload_file(local_p, f):
                total_uploaded += 1
            else:
                failed_files.append(f)
            
    for d in DIRS_TO_SYNC:
        dir_p = os.path.join(BASE_DIR, d)
        if not os.path.exists(dir_p):
            continue
        for root, dirs, files in os.walk(dir_p):
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root or ".git" in root:
                    continue
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, BASE_DIR)
                if upload_file(local_path, rel_path):
                    total_uploaded += 1
                else:
                    failed_files.append(rel_path)
                
    print(f"\nDone! Uploaded total {total_uploaded} files to PythonAnywhere.")
    if failed_files:
        print(f"WARNING: {len(failed_files)} files failed to upload: {failed_files}")
    else:
        print("PERFECT 100% SUCCESS: All files uploaded without a single error!")
    
    # Reload WebApp
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"Webapp reload status: {r_reload.status_code}")

if __name__ == "__main__":
    sync_all()

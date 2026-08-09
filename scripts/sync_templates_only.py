import os
import sys
import time
import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")

def upload_file(local_path, rel_path):
    cloud_path = f"/home/{USERNAME}/jobhunt/{rel_path.replace('\\', '/')}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{cloud_path}"
    
    with open(local_path, "rb") as f:
        content = f.read()
        
    for attempt in range(5):
        try:
            r = requests.post(url, headers=HEADERS, files={"content": content}, timeout=15)
            if r.status_code in (200, 201):
                print(f"[OK 200] Uploaded: {rel_path}")
                time.sleep(0.4)
                return True
            elif r.status_code == 429:
                print(f"[429 Rate Limit] Pausing 5s before retrying {rel_path}...")
                time.sleep(5)
            else:
                print(f"[FAIL {r.status_code}] {rel_path}: {r.text[:100]}")
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Exception uploading {rel_path}: {e}")
            time.sleep(2)
    return False

def sync_remaining_templates():
    print("Starting targeted sync of Jinja2 templates to PythonAnywhere...")
    total_uploaded = 0
    
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in sorted(files):
            if file.endswith(".html") or file.endswith(".jinja2"):
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, BASE_DIR)
                if upload_file(local_path, rel_path):
                    total_uploaded += 1
                
    print(f"\nDone! Uploaded total {total_uploaded} template files to PythonAnywhere.")
    
    # Reload WebApp
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"Webapp reload status: {r_reload.status_code}")

if __name__ == "__main__":
    sync_remaining_templates()

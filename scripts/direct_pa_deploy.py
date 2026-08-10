import os
import sys
import time
import zipfile
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(PROJECT_ROOT, "deploy_bundle.zip")

EXCLUDE_DIRS = {
    ".git", ".venv", ".venv2", "node_modules", ".pytest_cache", "__pycache__",
    "archive", "cache", ".agents", ".gemini", "brain", "frontend", "data", "logs",
    "tmp", "coverage", ".next", "dist", "build", "assets", "uploads"
}
EXCLUDE_EXTS = {".pyc", ".db", ".log", ".sqlite", ".sqlite3", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg", ".pdf", ".mp4", ".exe"}

def create_bundle():
    print(f"[*] Packaging project files from {PROJECT_ROOT}...")
    file_count = 0
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS or file.startswith('.'):
                    continue
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, PROJECT_ROOT)
                zipf.write(abs_file, rel_file)
                file_count += 1
    size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
    print(f"[✓] Created {ZIP_PATH} with {file_count} files ({size_mb:.2f} MB)")

def upload_and_extract():
    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. Upload zip bundle to PythonAnywhere
    remote_zip_path = f"/home/{USERNAME}/jobhunt/deploy_bundle.zip"
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_zip_path}"
    print(f"[*] Uploading deploy_bundle.zip to PythonAnywhere ({remote_zip_path})...")
    
    with open(ZIP_PATH, 'rb') as f:
        r_up = session.post(upload_url, files={"content": f}, timeout=120)
    
    if r_up.status_code in (200, 201):
        print(f"[✓] Zip uploaded successfully (HTTP {r_up.status_code})")
    else:
        print(f"[!] Upload failed with status {r_up.status_code}: {r_up.text}")
        return False

    # 2. Get active console or create new bash console
    print("[*] Accessing PythonAnywhere Bash Console...")
    r_consoles = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
    consoles = r_consoles.json() if r_consoles.status_code == 200 else []
    
    console_id = None
    if isinstance(consoles, list) and len(consoles) > 0:
        console_id = consoles[0]["id"]
        print(f"[*] Using existing console ID: {console_id}")
    else:
        r_create = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
        if r_create.status_code in (200, 201):
            console_id = r_create.json()["id"]
            print(f"[✓] Created new console ID: {console_id}")
        else:
            print(f"[!] Failed to create console: {r_create.text}")
            return False

    # 3. Send extract and reload commands
    unzip_cmd = (
        "cd /home/JHFGUF/jobhunt && "
        "python3 -c \"import zipfile; zipfile.ZipFile('deploy_bundle.zip').extractall('.')\" && "
        "rm -f deploy_bundle.zip && "
        "touch /var/www/jhfguf_pythonanywhere_com_wsgi.py\n"
    )
    print(f"[*] Executing extraction in console {console_id}...")
    r_send = session.post(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/",
        json={"input": unzip_cmd}
    )
    print(f"[*] Send input status: {r_send.status_code}")

    time.sleep(5)

    # 4. Read console output
    r_out = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/")
    if r_out.status_code == 200:
        output = r_out.json().get("output", "")
        print("=== Console Output snippet ===")
        print(output[-600:])
        print("==============================")

    # 5. Reload webapp
    print("[*] Triggering PythonAnywhere webapp reload...")
    r_reload = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] Webapp reload status: {r_reload.status_code}")

    # 6. Verify live site
    time.sleep(3)
    print("[*] Verifying live deployment...")
    try:
        r_live = requests.get(f"https://{DOMAIN}/ping", timeout=15)
        print(f"[✓] Live Ping Response: HTTP {r_live.status_code} -> {r_live.text[:100]}")
    except Exception as e:
        print(f"[!] Ping verification failed: {e}")

    # Cleanup local zip
    if os.path.exists(ZIP_PATH):
        try: os.remove(ZIP_PATH)
        except Exception: pass

    return True

if __name__ == "__main__":
    create_bundle()
    upload_and_extract()

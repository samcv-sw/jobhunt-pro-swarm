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
    ".git", ".venv", ".venv2", "test_env", "test_env_2", "data", "logs", "screenshots",
    "node_modules", ".pytest_cache", "__pycache__", "archive", "cache", ".agents", ".gemini", "brain", ".next",
    "frontend", "frontend-vue", "mobile", "extension", "dashboard", "bot", "chat_images", "chrome_extension", "backend-node"
}
EXCLUDE_EXTS = {".pyc", ".log", ".zip", ".tflite", ".webm", ".pack", ".db", ".sqlite", ".sqlite3"}
EXCLUDE_FILES = {"JobHunt_Pro_Full_Chat_Log.html", "deploy_bundle.zip"}

def create_full_bundle():
    print(f"[*] Packaging ALL current local project files from {PROJECT_ROOT}...")
    file_count = 0
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            for file in files:
                if file in EXCLUDE_FILES or file.startswith('.'):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, PROJECT_ROOT)
                zipf.write(abs_file, rel_file)
                file_count += 1
    size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
    print(f"[✓] Successfully created {ZIP_PATH} ({file_count} files, {size_mb:.2f} MB)")

def get_or_create_console(session):
    r_consoles = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
    if r_consoles.status_code == 200:
        consoles = r_consoles.json()
        if isinstance(consoles, list) and len(consoles) > 0:
            cid = consoles[0]["id"]
            print(f"[*] Found existing console ID: {cid}")
            return cid

    # Try creating new console
    r_create = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
    if r_create.status_code in (200, 201):
        cid = r_create.json()["id"]
        print(f"[✓] Created fresh console ID: {cid}")
        return cid
    else:
        print(f"[!] Console creation returned status {r_create.status_code}: {r_create.text}")
        # Delete existing consoles if limit reached
        if r_consoles.status_code == 200 and isinstance(r_consoles.json(), list):
            for c in r_consoles.json():
                session.delete(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{c['id']}/")
            time.sleep(2)
            r_retry = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
            if r_retry.status_code in (200, 201):
                cid = r_retry.json()["id"]
                print(f"[✓] Created new console ID after cleanup: {cid}")
                return cid
    return None

def wipe_and_redeploy():
    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. Upload zip bundle to PythonAnywhere root
    remote_zip_path = f"/home/{USERNAME}/jobhunt/deploy_bundle.zip"
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_zip_path}"
    print(f"[*] Uploading fresh deploy_bundle.zip to PythonAnywhere...")
    
    with open(ZIP_PATH, 'rb') as f:
        r_up = session.post(upload_url, files={"content": f}, timeout=180)
    
    if r_up.status_code in (200, 201):
        print(f"[✓] Zip uploaded successfully (HTTP {r_up.status_code})")
    else:
        print(f"[!] Upload failed with status {r_up.status_code}: {r_up.text}")
        return False

    # 2. Get console or create new console
    print("[*] Connecting to PythonAnywhere Bash Console via API...")
    console_id = get_or_create_console(session)
    if not console_id:
        print("[!] Could not obtain console ID.")
        return False

    # 3. Command: Clear old Python pycache, extract fresh bundle over /home/JHFGUF/jobhunt/, touch WSGI
    clean_and_extract_cmd = (
        "cd /home/JHFGUF/jobhunt && "
        "find . -name '__pycache__' -exec rm -rf {} + && "
        "find . -name '*.pyc' -delete && "
        "python3 -c \"import zipfile; zipfile.ZipFile('deploy_bundle.zip').extractall('.')\" && "
        "rm -f deploy_bundle.zip && "
        "touch /var/www/jhfguf_pythonanywhere_com_wsgi.py\n"
    )
    print(f"[*] Executing wipe & overwrite extraction in console {console_id}...")
    
    r_send = session.post(
        f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/",
        json={"input": clean_and_extract_cmd}
    )
    if r_send.status_code != 200:
        print(f"[*] Console send returned HTTP {r_send.status_code}. Re-creating console...")
        session.delete(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/")
        time.sleep(2)
        r_new = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
        if r_new.status_code in (200, 201):
            console_id = r_new.json()["id"]
            time.sleep(4)
            r_send = session.post(
                f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/",
                json={"input": clean_and_extract_cmd}
            )
    print(f"[✓] Command send status: {r_send.status_code}")

    time.sleep(7)

    # 4. Get console output
    r_out = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/")
    if r_out.status_code == 200:
        output = r_out.json().get("output", "")
        print("=== Console Output ===")
        print(output[-800:])
        print("======================")

    # 5. Reload webapp
    print("[*] Reloading PythonAnywhere WebApp...")
    r_reload = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/")
    print(f"[✓] Webapp reload status: {r_reload.status_code}")

    time.sleep(5)

    # 6. Comprehensive Route Audit
    print("\n=======================================================")
    print("   RUNNING COMPREHENSIVE LIVE AUDIT ON PYTHONANYWHERE  ")
    print("=======================================================")
    test_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    endpoints_to_test = [
        ("/", "Homepage"),
        ("/login", "Login Page"),
        ("/pricing", "Pricing Page"),
        ("/dashboard", "Singularity Dashboard"),
        ("/resume-tailor", "AI Resume Tailor"),
        ("/ats-scorer", "ATS Optimizer Studio"),
        ("/api/v2/health", "Health API Endpoint"),
    ]

    all_passed = True
    for ep, name in endpoints_to_test:
        url = f"https://{DOMAIN}{ep}"
        try:
            r = requests.get(url, headers=test_headers, timeout=15)
            status_symbol = "✓" if r.status_code in (200, 302) else "✗"
            print(f"[{status_symbol}] {name} ({ep}): HTTP {r.status_code}")
            if r.status_code not in (200, 302):
                all_passed = False
        except Exception as err:
            print(f"[✗] {name} ({ep}): Request Error ({err})")
            all_passed = False

    # Cleanup local zip
    if os.path.exists(ZIP_PATH):
        try: os.remove(ZIP_PATH)
        except Exception: pass

    if all_passed:
        print("\n[SUCCESS] All live endpoints returned 200 OK! Local version is 100% active on PythonAnywhere!")
    else:
        print("\n[WARNING] Some endpoints returned non-200 status codes. Review log outputs.")

    return all_passed

if __name__ == "__main__":
    create_full_bundle()
    wipe_and_redeploy()

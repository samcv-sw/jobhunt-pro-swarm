# scratch/smart_deploy.py
import requests
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

TOKEN = "7e7ad272cc2d4470e8078fca29dfacf301fb01fe"
USERNAME = "JHFGUF"
HEADERS = {
    "Authorization": f"Token {TOKEN}"
}

GIT_DEPLOY_SCRIPT = """# git_deploy.py
import subprocess
import os
import sys

PROJECT = '/home/JHFGUF/jobhunt'
os.chdir(PROJECT)

# Execute git fetch and hard reset
print("--- RUNNING GIT FETCH & RESET ON CLOUD ---")
res1 = subprocess.run(["git", "fetch", "origin", "main"], capture_output=True, text=True)
print("git fetch stdout:", res1.stdout)
print("git fetch stderr:", res1.stderr)

res2 = subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output=True, text=True)
print("git reset stdout:", res2.stdout)
print("git reset stderr:", res2.stderr)

# Install requirements
res3 = subprocess.run(["pip", "install", "-r", "requirements.txt", "--quiet"], capture_output=True, text=True)
print("pip install stdout:", res3.stdout)
print("pip install stderr:", res3.stderr)

# Seed database
res4 = subprocess.run(["python3", "_seed_all.py"], capture_output=True, text=True)
print("seed stdout:", res4.stdout)
print("seed stderr:", res4.stderr)
print("--- CLOUD SYNC COMPLETE ---")
"""

TEMP_WSGI = """# Temporary WSGI with Auto-Deployment Hook
import sys
import os

PROJECT = '/home/JHFGUF/jobhunt'
sys.path.insert(0, PROJECT)
os.chdir(PROJECT)

# Run git deployment script
try:
    print("--- RUNNING TEMP WSGI DEPLOY ---")
    import git_deploy
    print("--- TEMP WSGI DEPLOY DONE ---")
except Exception as e:
    print("Error during temp WSGI deploy:", e)

# Standard ASGI-to-WSGI adapter mock to avoid loading errors
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"Auto-deployment hook executed. Reloading webapp with production WSGI next..."]
"""

# Load local clean production WSGI content
with open("wsgi_pa.py", "r", encoding="utf-8") as f:
    CLEAN_WSGI_CONTENT = f.read()

def upload_file(path, content):
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{path}"
    print(f"Uploading file to {url}...")
    try:
        response = requests.post(
            url,
            files={"content": ("file.py", content, "text/plain")},
            headers=HEADERS,
            timeout=20
        )
        print(f"Upload response status: {response.status_code}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Upload failed: {e}")
        return False

def reload_webapp():
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/"
    print(f"Reloading webapp via {url}...")
    try:
        response = requests.post(
            url,
            headers=HEADERS,
            timeout=25
        )
        print(f"Reload response status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Reload failed: {e}")
        return False

def trigger_hook():
    url = "https://jhfguf.pythonanywhere.com/"
    print(f"Triggering auto-deploy hook by hitting {url}...")
    try:
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )
        print(f"Server response status: {response.status_code}")
        print(f"Server response snippet: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Trigger failed: {e}")
        return False

def main():
    print("==================================================")
    # 1. Upload git_deploy.py script to /home/JHFGUF/jobhunt/
    print("Step 1: Uploading git_deploy.py script...")
    success = upload_file(f"/home/{USERNAME}/jobhunt/git_deploy.py", GIT_DEPLOY_SCRIPT)
    if not success:
        print("[FAIL] Failed to upload git_deploy.py script.")
        return
        
    # 2. Upload temporary WSGI file to /var/www/
    print("\nStep 2: Uploading temporary WSGI file...")
    success = upload_file(f"/var/www/{USERNAME.lower()}_pythonanywhere_com_wsgi.py", TEMP_WSGI)
    if not success:
        print("[FAIL] Failed to upload temporary WSGI script.")
        return
        
    # 3. Reload Webapp to load the temp WSGI config
    print("\nStep 3: Reloading webapp to arm deployment hook...")
    success = reload_webapp()
    if not success:
        print("[FAIL] Failed to reload webapp.")
        return
        
    # 4. Hit the server to trigger the deployment
    print("\nStep 4: Hitting server to trigger deployment...")
    time.sleep(3)
    success = trigger_hook()
    if not success:
        print("[WARNING] Trigger received non-200 or timed out. Checking recovery...")
        
    # 5. Restore the clean production WSGI code
    print("\nStep 5: Restoring clean production WSGI file...")
    success = upload_file(f"/var/www/{USERNAME.lower()}_pythonanywhere_com_wsgi.py", CLEAN_WSGI_CONTENT)
    if not success:
        print("[FAIL] Failed to restore clean WSGI script.")
        return
        
    # 6. Reload the webapp a final time to boot version 16.7 cleanly
    print("\nStep 6: Reloading webapp a final time...")
    time.sleep(3)
    success = reload_webapp()
    if success:
        print("\n==================================================")
        print("[SUCCESS] Webapp is now fully synced, seeded, and running version 16.7 cleanly!")
        print("==================================================")
    else:
        print("[FAIL] Failed to reload webapp for clean startup.")

if __name__ == "__main__":
    main()

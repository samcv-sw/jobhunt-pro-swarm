import os
import sys

import requests

sys.stdout.reconfigure(encoding='utf-8')

TOKENS = [
    "7e7ad272cc2d4470e8078fca29dfacf301fb01fe", # Token 1
    "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"  # Token 2
]
USERNAME = "JHFGUF"
REMOTE_ROOT = f"/home/{USERNAME}/jobhunt"
LOCAL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Let's find which token is valid first
def get_working_token():
    for i, tok in enumerate(TOKENS):
        headers = {"Authorization": f"Token {tok}"}
        url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/cpu/"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                print(f"Token {i+1} is VALID!")
                return tok
            else:
                print(f"Token {i+1} returned status code {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"Token {i+1} check failed: {e}")
    return None

token = get_working_token()
if not token:
    print("CRITICAL: No working token found!")
    sys.exit(1)

HEADERS = {"Authorization": f"Token {token}"}

FILES_TO_DEPLOY = [
    ("core/smart_scheduler.py", f"{REMOTE_ROOT}/core/smart_scheduler.py"),
    ("core/multi_tenant.py", f"{REMOTE_ROOT}/core/multi_tenant.py"),
    ("core/email_engine.py", f"{REMOTE_ROOT}/core/email_engine.py"),
    ("core/campaign_runner.py", f"{REMOTE_ROOT}/core/campaign_runner.py"),
    ("core/lightning_runner.py", f"{REMOTE_ROOT}/core/lightning_runner.py"),
    ("core/pa_job_scraper.py", f"{REMOTE_ROOT}/core/pa_job_scraper.py"),
    ("core/anti_ban.py", f"{REMOTE_ROOT}/core/anti_ban.py"),
    ("core/ats_matcher.py", f"{REMOTE_ROOT}/core/ats_matcher.py"),
    ("core/ats_scorer.py", f"{REMOTE_ROOT}/core/ats_scorer.py"),
    ("core/personalizer.py", f"{REMOTE_ROOT}/core/personalizer.py"),
    ("core/scam_detector.py", f"{REMOTE_ROOT}/core/scam_detector.py"),
    ("core/semantic_cache.py", f"{REMOTE_ROOT}/core/semantic_cache.py"),
    ("web/cloud_tick_router.py", f"{REMOTE_ROOT}/web/cloud_tick_router.py"),
    ("cloud_orchestrator.py", f"{REMOTE_ROOT}/cloud_orchestrator.py"),
]

def upload_file(local_path, remote_path):
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
    print(f"Uploading {local_path} -> {remote_path}...")
    if not os.path.exists(local_path):
        print(f"  ❌ LOCAL FILE NOT FOUND: {local_path}")
        return False
        
    with open(local_path, "rb") as f:
        content = f.read()
        
    try:
        r = requests.post(
            url,
            files={"content": (os.path.basename(local_path), content, "application/octet-stream")},
            headers=HEADERS,
            timeout=120
        )
        if r.status_code in (200, 201):
            print(f"  ✅ Uploaded (HTTP {r.status_code})")
            return True
        else:
            print(f"  ❌ FAILED (HTTP {r.status_code}): {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def reload_webapp():
    # Try reloading by domain name
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/"
    print(f"Reloading webapp via {url}...")
    try:
        r = requests.post(url, headers=HEADERS, timeout=30)
        if r.status_code in (200, 204):
            print("  ✅ Webapp reloaded successfully!")
            return True
        else:
            print(f"  ❌ Reload failed (HTTP {r.status_code}): {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ Reload error: {e}")
        return False

print("\n--- Starting Upload of All Core Files ---")
ok_count = 0
for rel_path, remote_path in FILES_TO_DEPLOY:
    local_path = os.path.join(LOCAL_ROOT, rel_path.replace("/", os.sep))
    if upload_file(local_path, remote_path):
        ok_count += 1
        
print(f"\nUpload summary: {ok_count}/{len(FILES_TO_DEPLOY)} files uploaded successfully.")

if ok_count > 0:
    reload_webapp()

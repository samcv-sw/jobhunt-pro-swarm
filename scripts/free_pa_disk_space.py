import sys
import time
import requests

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

file_targets = [
    f"/home/{USERNAME}/jobhunt/JobHunt_Pro_Full_Chat_Log.html",
    f"/home/{USERNAME}/jobhunt/deploy_bundle.zip",
    f"/home/{USERNAME}/jobhunt/JobHunt_Pro_Full_Chat_Log.md",
    f"/home/{USERNAME}/jobhunt/JobHunt_Pro_Full_Chat_Log.txt",
    f"/home/{USERNAME}/jobhunt/data/audit_security.db",
    f"/home/{USERNAME}/jobhunt/data/master_analytics.db",
    f"/home/{USERNAME}/jobhunt/data/enterprise_b2b.db",
    f"/home/{USERNAME}/jobhunt/data/saas_metrics.db",
    f"/home/{USERNAME}/jobhunt/data/test_db.db",
    f"/home/{USERNAME}/jobhunt/data/gcc_b2b_swarms.db",
    f"/home/{USERNAME}/jobhunt/data/jobhunt_saas.db",
    f"/home/{USERNAME}/jobhunt/web/git_pull_log.txt",
    f"/home/{USERNAME}/jobhunt/web/db_unlock_log.txt",
]

print("=== Smart Disk Quota Cleanup on PythonAnywhere ===")
deleted_count = 0

for f_path in file_targets:
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{f_path}"
    deleted = False
    for attempt in range(5):
        try:
            res = requests.delete(url, headers=HEADERS, timeout=15)
            if res.status_code in (200, 204):
                print(f"[SUCCESS 204] Deleted bloat: {f_path}")
                deleted_count += 1
                deleted = True
                time.sleep(1.5)
                break
            elif res.status_code == 404:
                print(f"[404 Not Found] Skip: {f_path}")
                break
            elif res.status_code == 429:
                print(f"[429 Rate Limit] Retrying {f_path} in 4s...")
                time.sleep(4)
            else:
                print(f"[{res.status_code}] Failed: {f_path}: {res.text[:60]}")
                time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Exception deleting {f_path}: {e}")
            time.sleep(2)

print(f"\n[✓] Cleanup complete: {deleted_count} large bloat files removed!")

# Trigger Webapp Reload
time.sleep(2)
r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
print(f"[✓] Webapp Reload Status: {r_reload.status_code}")

import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Targets to delete via file API to free disk space immediately
file_targets = [
    f"/home/{USERNAME}/jobhunt/JobHunt_Pro_Full_Chat_Log.txt",
    f"/home/{USERNAME}/jobhunt/data/audit_security.db",
    f"/home/{USERNAME}/jobhunt/data/master_analytics.db",
    f"/home/{USERNAME}/jobhunt/data/enterprise_b2b.db",
    f"/home/{USERNAME}/jobhunt/data/saas_metrics.db",
    f"/home/{USERNAME}/jobhunt/data/test_db.db",
    f"/home/{USERNAME}/jobhunt/data/gcc_b2b_swarms.db",
    f"/home/{USERNAME}/jobhunt/data/jobhunt_saas.db",
    f"/home/{USERNAME}/test_clean.txt",
    f"/home/{USERNAME}/test_space.txt",
    f"/home/{USERNAME}/disk_usage.txt",
    f"/home/{USERNAME}/quota.txt"
]

print("Deleting bloat files...")
for f in file_targets:
    r = SESSION.delete(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{f}")
    if r.status_code == 204:
        print(f"Deleted: {f}")

print("Testing WSGI update status post cleanup...")
with open("scripts/update_pa_wsgi_sync.py", "r", encoding="utf-8") as f:
    code = f.read()

# Run update_wsgi
import scripts.update_pa_wsgi_sync as w
w.update_wsgi()

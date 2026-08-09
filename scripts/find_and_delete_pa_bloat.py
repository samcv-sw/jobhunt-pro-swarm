import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Known large file paths to remove if they exist
targets = [
    f"/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db",
    f"/home/{USERNAME}/jobhunt/data/jobhunt_saas.db",
    f"/home/{USERNAME}/jobhunt/data/master_analytics.db",
    f"/home/{USERNAME}/jobhunt/data/enterprise_b2b.db",
    f"/home/{USERNAME}/jobhunt/data/audit_security.db",
    f"/home/{USERNAME}/jobhunt/data/ai_agents.db",
    f"/home/{USERNAME}/jobhunt/data/saas_metrics.db",
    f"/home/{USERNAME}/jobhunt/data/test_db.db",
    f"/home/{USERNAME}/jobhunt/data/gcc_b2b_swarms.db",
    f"/home/{USERNAME}/test_clean.txt",
    f"/home/{USERNAME}/test_api_upload.txt",
    f"/home/{USERNAME}/disk_usage.txt",
    f"/home/{USERNAME}/quota.txt"
]

print("Deleting target files from PythonAnywhere...")
for t in targets:
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{t}"
    r = SESSION.delete(url)
    if r.status_code == 204:
        print(f"Deleted: {t}")

print("Testing file upload after deletion...")
r_test = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/test_space.txt", files={"content": b"hello"})
print(f"Upload status: {r_test.status_code}")

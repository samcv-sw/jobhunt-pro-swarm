"""Deploy fixed files to PythonAnywhere PA using correct multipart API."""
import requests, sys, os
sys.stdout.reconfigure(encoding='utf-8')

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
PA_USER = "JHFGUF"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}"
HEADERS_MUL = {"Authorization": f"Token {PA_TOKEN}"}

def upload_file_multipart(remote_path, local_path):
    """Upload using multipart form-data with field name 'content'."""
    with open(local_path, 'rb') as f:
        content_bytes = f.read()
    
    url = f"{BASE_URL}/files/path/{remote_path}/"
    files = {'content': (remote_path.split('/')[-1], content_bytes, 'text/plain')}
    resp = requests.post(url, headers=HEADERS_MUL, files=files, timeout=60)
    return resp.status_code, resp.text[:200]

def reload_webapp():
    resp = requests.post(
        f"{BASE_URL}/webapps/3072814/reload/",
        headers={"Authorization": f"Token {PA_TOKEN}"},
        timeout=30
    )
    return resp.status_code, resp.text[:200]

BASE_LOCAL = r"C:\Users\samde\Desktop\cv sam new ma3 kimi"

print("=== Uploading files to PA ===")
files = [
    ("jobhunt/core/email_engine.py", os.path.join(BASE_LOCAL, "core", "email_engine.py")),
    ("jobhunt/cloud_orchestrator.py", os.path.join(BASE_LOCAL, "cloud_orchestrator.py")),
]

for remote, local in files:
    status, text = upload_file_multipart(remote, local)
    ok = status in (200, 201)
    print(f"{'OK' if ok else 'FAIL'} {status} {remote}")
    if not ok:
        print(f"   {text}")

print("\n=== Reloading webapp ===")
status, text = reload_webapp()
print(f"Reload: {status}")
if status not in (200, 204):
    print(f"  {text}")
else:
    print("Reload OK!")

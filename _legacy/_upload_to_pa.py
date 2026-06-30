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
    
    url = f"{BASE_URL}/files/path/home/JHFGUF/{remote_path}"
    files = {'content': (remote_path.split('/')[-1], content_bytes, 'text/plain')}
    resp = requests.post(url, headers=HEADERS_MUL, files=files, timeout=60)
    return resp.status_code, resp.text[:200]

def reload_webapp():
    resp = requests.post(
        f"{BASE_URL}/webapps/jhfguf.pythonanywhere.com/reload/",
        headers={"Authorization": f"Token {PA_TOKEN}"},
        timeout=30
    )
    return resp.status_code, resp.text[:200]

BASE_LOCAL = os.path.dirname(os.path.abspath(__file__))

print("=== Uploading files to PA ===")
files = [
    ("jobhunt/web/app_v2.py", os.path.join(BASE_LOCAL, "web", "app_v2.py")),
    ("jobhunt/web/templates/pricing_v3.html", os.path.join(BASE_LOCAL, "web", "templates", "pricing_v3.html")),
    ("jobhunt/web/static/css/dashboard-v4.css", os.path.join(BASE_LOCAL, "web", "static", "css", "dashboard-v4.css")),
    ("jobhunt/web/static/css/style.css", os.path.join(BASE_LOCAL, "web", "static", "css", "style.css")),
    ("jobhunt/web/static/css/landing-v4.css", os.path.join(BASE_LOCAL, "web", "static", "css", "landing-v4.css")),
    ("jobhunt/web/static/css/cyberpunk.css", os.path.join(BASE_LOCAL, "web", "static", "css", "cyberpunk.css")),
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

"""Deploy fixed files to PythonAnywhere PA using Files API."""
import requests, sys, os
sys.stdout.reconfigure(encoding='utf-8')

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
PA_USER = "JHFGUF"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}"
HEADERS = {
    "Authorization": f"Token {PA_TOKEN}",
    "Content-Type": "application/json"
}

def upload_file(remote_path, local_path):
    """Upload a file using PA Files API."""
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try POST first (create)
    url = f"{BASE_URL}/files/contents/"
    payload = {"path": remote_path, "content": content}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    print(f"POST {remote_path}: {resp.status_code}")
    if resp.status_code in (200, 201):
        return True
    if resp.status_code == 400:
        # Already exists, try PUT
        url2 = f"{BASE_URL}/files/path/home/jhfguf/{remote_path}"
        # PythonAnywhere API expects multipart form-data for /files/path/...
        files = {'content': (remote_path.split('/')[-1], content.encode("utf-8"), 'text/plain')}
        resp2 = requests.post(url2, headers={"Authorization": f"Token {PA_TOKEN}"}, files=files, timeout=60)
        print(f"  PUT {remote_path}: {resp2.status_code}")
        return resp2.status_code in (200, 201)
    print(f"  Error: {resp.text[:200]}")
    return False

def reload_webapp():
    """Reload PA webapp via API."""
    resp = requests.post(
        f"{BASE_URL}/webapps/3072814/reload/",
        headers={"Authorization": f"Token {PA_TOKEN}"},
        timeout=30
    )
    print(f"Reload webapp: {resp.status_code}")
    if resp.status_code != 200 and resp.status_code != 204:
        print(f"  Error: {resp.text[:200]}")
    return resp.status_code in (200, 204)

def test_cloud_tick():
    """Test the cloud tick endpoint."""
    resp = requests.get("https://jhfguf.pythonanywhere.com/api/v2/cloud-tick/status", timeout=15)
    print(f"Cloud tick status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.json())
    return resp.status_code == 200

BASE_LOCAL = os.path.dirname(os.path.abspath(__file__))

# Upload core files
print("=== Deploying to PA ===")
files = [
    ("jobhunt/web/templates/pricing_v3.html", os.path.join(BASE_LOCAL, "web", "templates", "pricing_v3.html")),
]

for remote, local in files:
    upload_file(remote, local)

print("\n=== Reloading Webapp ===")
reload_webapp()

#!/usr/bin/env python3
"""Upload + Bootstrap campaign on PA"""
import urllib.request, json, time, ssl, os

PA_TOKEN = "34fe3a4cafefe3a4ac8d592119d5480a0b988971"
USER = "JHFGUF"

def upload_file(local_path, remote_path):
    url = f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path{remote_path}"
    boundary = "----BOUNDARY123XYZ"
    with open(local_path, 'rb') as f:
        file_content = f.read()
    body_parts = []
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(f'Content-Disposition: form-data; name="content"; filename="{os.path.basename(local_path)}"'.encode())
    body_parts.append(b'Content-Type: application/octet-stream')
    body_parts.append(b'')
    body_parts.append(file_content)
    body_parts.append(f'--{boundary}--'.encode())
    body = b'\r\n'.join(body_parts)
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header("Authorization", f"Token {PA_TOKEN}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

def reload_webapp():
    url = f"https://www.pythonanywhere.com/api/v0/user/{USER}/webapps/jhfguf.pythonanywhere.com/reload/"
    req = urllib.request.Request(url, data=b'', method='POST')
    req.add_header("Authorization", f"Token {PA_TOKEN}")
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

# Upload app_v2.py
local = r"C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py"
remote = "/home/JHFGUF/jobhunt/web/app_v2.py"

print(f"Uploading app_v2.py ({os.path.getsize(local)} bytes)...")
s, r = upload_file(local, remote)
print(f"Upload: {s} {'✅' if s==200 else '❌'}")

print("Reloading...")
s, r = reload_webapp()
print(f"Reload: {s} {'✅' if s==200 else '❌'}")

time.sleep(3)

# Bootstrap
print("\nBootstrapping campaign...")
ctx = ssl.create_default_context()
try:
    req = urllib.request.Request(
        "https://jhfguf.pythonanywhere.com/api/admin/bootstrap?key=jobhunt-cron-secret-2026",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    result = json.loads(resp.read().decode())
    print(f"✅ Bootstrap: {json.dumps(result, indent=2)}")
    
    if result.get("campaign_id"):
        # Trigger cron
        print("\nTriggering cron to process campaign...")
        req2 = urllib.request.Request(
            "https://jhfguf.pythonanywhere.com/api/cron/tick?reset=cooldown",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp2 = urllib.request.urlopen(req2, timeout=300, context=ctx)
        result2 = json.loads(resp2.read().decode())
        print(f"Cron: {json.dumps(result2, indent=2)}")
        
        # Final stats
        req3 = urllib.request.Request(
            "https://jhfguf.pythonanywhere.com/api/dashboard/stats",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp3 = urllib.request.urlopen(req3, timeout=15, context=ctx)
        print(f"\nFinal stats: {resp3.read().decode()}")
except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.read().decode()[:500]}")
except Exception as e:
    print(f"❌ Error: {e}")

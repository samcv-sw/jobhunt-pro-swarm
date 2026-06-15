#!/usr/bin/env python3
"""Upload app_v2.py to PA via correct API method (POST multipart)"""
import urllib.request, json, time, ssl, os

PA_TOKEN = "34fe3a4cafefe3a4ac8d592119d5480a0b988971"
USER = "JHFGUF"

def upload_file(local_path, remote_path):
    """Upload file via PA API using multipart POST"""
    url = f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path{remote_path}"
    
    boundary = "----BOUNDARY123XYZ"
    
    with open(local_path, 'rb') as f:
        file_content = f.read()
    
    # Build multipart body
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
        result = resp.read().decode()
        print(f"✅ Upload success: {resp.status}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"❌ HTTP {e.code}: {body}")
        return False

def reload_webapp():
    """Reload webapp"""
    url = f"https://www.pythonanywhere.com/api/v0/user/{USER}/webapps/jhfguf.pythonanywhere.com/reload/"
    req = urllib.request.Request(url, data=b'', method='POST')
    req.add_header("Authorization", f"Token {PA_TOKEN}")
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        print(f"✅ Reload: {resp.status}")
        return True
    except urllib.error.HTTPError as e:
        print(f"❌ Reload {e.code}: {e.read().decode()[:200]}")
        return False

# Upload app_v2.py
local = r"C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py"
remote = "/home/JHFGUF/jobhunt/web/app_v2.py"

print("=" * 60)
print("UPLOADING app_v2.py (" + str(os.path.getsize(local)) + " bytes)")
print("=" * 60)

if upload_file(local, remote):
    print("\nReloading...")
    reload_webapp()
    
    print("\nWaiting 3s...")
    time.sleep(3)
    
    # Try bootstrap
    print("\n" + "=" * 60)
    print("CALLING BOOTSTRAP")
    print("=" * 60)
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(
            "https://jhfguf.pythonanywhere.com/api/admin/bootstrap?key=jobhunt-cron-secret-2026",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        result = json.loads(resp.read().decode())
        print(f"✅ {json.dumps(result, indent=2)}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()[:500]}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n✅ DONE")

#!/usr/bin/env python3
"""Deploy app_v2.py with bootstrap endpoint to PA"""
import urllib.request, json, time, ssl

PA_TOKEN = "34fe3a4cafefe3a4ac8d592119d5480a0b988971"
USER = "JHFGUF"
FILE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path/home/{USER}/jobhunt/web/app_v2.py"
RELOAD_URL = f"https://www.pythonanywhere.com/api/v0/user/{USER}/webapps/jhfguf.pythonanywhere.com/reload/"

app_v2_path = r"C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py"

def put_file(file_path, remote_url):
    """Upload file to PA via PUT"""
    with open(file_path, 'rb') as f:
        content = f.read()
    
    req = urllib.request.Request(remote_url, data=content, method='PUT')
    req.add_header("Authorization", f"Token {PA_TOKEN}")
    req.add_header("Content-Type", "application/octet-stream")
    
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

def post_reload():
    """Reload webapp"""
    req = urllib.request.Request(RELOAD_URL, data=b"", method='POST')
    req.add_header("Authorization", f"Token {PA_TOKEN}")
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

# Step 1: Upload
print("=" * 60)
print("STEP 1: UPLOAD app_v2.py")
print("=" * 60)
status, resp = put_file(app_v2_path, FILE_URL)
print(f"Upload: {status} {'✅' if status in (200,201,204) else '❌'}")
print(f"Response: {resp[:100]}")

# Step 2: Reload
print("\n" + "=" * 60)
print("STEP 2: RELOAD WEBAPP")
print("=" * 60)
status, resp = post_reload()
print(f"Reload: {status} {'✅' if status==200 else '❌'}")
if status != 200:
    print(f"Response: {resp}")

# Step 3: Wait for reload
print("\nWaiting 3s for reload...")
time.sleep(3)

# Step 4: Call bootstrap
print("\n" + "=" * 60)
print("STEP 3: BOOTSTRAP USER + CAMPAIGN")
print("=" * 60)
ctx = ssl.create_default_context()
try:
    req = urllib.request.Request(
        "https://jhfguf.pythonanywhere.com/api/admin/bootstrap?key=jobhunt-cron-secret-2026",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    result = json.loads(resp.read().decode())
    print(f"Bootstrap: {json.dumps(result, indent=2)}")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"HTTP {e.code}: {body[:500]}")
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")
except Exception as e:
    print(f"Error: {e}")

# Step 5: Trigger cron
print("\n" + "=" * 60)
print("STEP 4: TRIGGER CRON")
print("=" * 60)
try:
    req = urllib.request.Request(
        "https://jhfguf.pythonanywhere.com/api/cron/tick?reset=cooldown",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=300, context=ctx)
    result = json.loads(resp.read().decode())
    print(f"Cron: {json.dumps(result, indent=2)}")
    if result.get("actions"):
        print("\n✅ Campaign started! Emails being sent!")
    if result.get("sent", 0) > 0:
        print(f"📧 Sent: {result['sent']} emails this tick")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 6: Final stats
print("\n" + "=" * 60)
print("FINAL STATS")
print("=" * 60)
try:
    req = urllib.request.Request(
        "https://jhfguf.pythonanywhere.com/api/dashboard/stats",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    print(f"Stats: {resp.read().decode()}")
except Exception as e:
    print(f"Stats error: {e}")

print("\n✅ DEPLOY COMPLETE!")

#!/usr/bin/env python3
"""Register new user + create campaign on PA"""
import urllib.request, urllib.parse, http.cookiejar, re, sys

PA = "https://jhfguf.pythonanywhere.com"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0')]

def req(url, data=None, method='POST'):
    if data and isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    r = urllib.request.Request(url, data=data, method=method)
    try:
        return opener.open(r, timeout=30)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on {url}")
        body = e.read().decode('utf-8', errors='replace')
        if 'already' in body.lower():
            print("User likely already exists!")
        print(body[:300])
        return None

# Step 1: Register
print("=== REGISTER ===")
resp = req(f"{PA}/register", {
    'email': 'samatou683@gmail.com',
    'password': 'Test@123!@#',
    'name': 'Sam Salameh',
    'phone': '+961708411009',
    'company_name': '',
    'user_type': 'jobseeker',
    'ref': '',
    'selected_plan': 'starter'
})
if resp:
    print(f"Register Status: {resp.status}")
    print(f"URL after: {resp.url}")
    for c in cj:
        print(f"  Cookie: {c.name}={c.value[:50]}")
else:
    print("Registration failed, trying login instead...")
    # Try alternate passwords
    for pwd in ['Test@123!@#', 'Sam2026!', 'JobHunt2026', 'Network2026!']:
        print(f"\nTrying login with: {pwd}")
        resp = req(f"{PA}/login", {'email': 'samatou683@gmail.com', 'password': pwd})
        if resp:
            body = resp.read().decode('utf-8', errors='replace')
            if 'dashboard' in resp.url or '/dashboard' in body[:200]:
                print(f"LOGIN SUCCESS with: {pwd}")
                break
            else:
                print(f"Failed with: {pwd}")

# Check if we have cookies now
print("\n=== CURRENT COOKIES ===")
for c in cj:
    print(f"  {c.name} = {c.value[:50]}")

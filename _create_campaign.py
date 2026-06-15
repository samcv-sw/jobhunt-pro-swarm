#!/usr/bin/env python3
"""
Create JobHunt Pro campaign for Sam on PA
Login -> Create profile -> Create campaign -> Trigger cron
"""
import urllib.request, urllib.parse, json, http.cookiejar, re, ssl, sys

PA_BASE = "https://jhfguf.pythonanywhere.com"

# Disable SSL verification for dev (keep it)
# Cookie Jar for session
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0')]

def do_req(url, data=None, method='POST'):
    if data and isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        return opener.open(req, timeout=30)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on {url}")
        print(e.read().decode()[:500])
        return None

# Step 1: Login
print("=== STEP 1: LOGIN ===")
resp = do_req(f"{PA_BASE}/login", {
    'email': 'samatou683@gmail.com',
    'password': 'JobHunt4Pro#'
})
if resp:
    print(f"Login: {resp.status} - {resp.reason}")
    # Print the cookies
    for c in cj:
        print(f"  Cookie: {c.name}={c.value[:30]}...")
else:
    print("Login FAILED")
    sys.exit(1)

# Step 2: Check existing profiles
print("\n=== STEP 2: CHECK DASHBOARD ===")
resp = do_req(f"{PA_BASE}/dashboard", method='GET')
if resp:
    body = resp.read().decode('utf-8', errors='replace')
    # Look for existing campaigns / profiles
    match = re.search(r'campaign[_\s]id["\':\s]*([a-zA-Z0-9\-]+)', body, re.I)
    if match:
        print(f"Found existing campaign: {match.group(1)}")
    else:
        print("No existing campaigns found on dashboard")
    # Check for profile info
    if 'sam' in body.lower():
        print("Sam profile detected on dashboard")
    print("Dashboard response length:", len(body))
else:
    print("Dashboard check failed")

# Step 3: Try to create a campaign via new-campaign page
print("\n=== STEP 3: NEW CAMPAIGN PAGE ===")
resp = do_req(f"{PA_BASE}/new-campaign", method='GET')
if resp:
    body = resp.read().decode('utf-8', errors='replace')
    # Check if there are profiles
    profile_match = re.search(r'profile[_\s]id["\':\s]*(\d+)', body, re.I)
    if profile_match:
        print(f"Found profile ID: {profile_match.group(1)}")
    # Look for the form
    if 'create' in body.lower() or 'profile' in body.lower():
        print("Campaign creation form accessible")
    print("New campaign page length:", len(body))
else:
    print("New campaign page FAILED")

# Step 4: Try creating campaign
print("\n=== STEP 4: CREATE CAMPAIGN ===")
# First check what profiles exist  
resp = do_req(f"{PA_BASE}/create-campaign", {
    'profile_id': '1',
    'company_count': '50',
    'bouquet': 'starter',
    'bouquet_names': 'Network Engineer, IT Support, Senior Network Engineer'
}, method='POST')
if resp:
    url = resp.url
    body = resp.read().decode('utf-8', errors='replace')
    print(f"Response URL: {url}")
    print(f"Status: {resp.status}")
    cid_match = re.search(r'/campaign/([a-zA-Z0-9\-]+)', url)
    if cid_match:
        cid = cid_match.group(1)
        print(f"Campaign created! ID: {cid}")
    else:
        print("Campaign not created. Response snippet:", body[:500])
else:
    print("Create campaign FAILED")

# Step 5: Trigger cron
print("\n=== STEP 5: CRON TICK ===")
resp = do_req(f"{PA_BASE}/api/cron/tick?reset=cooldown", method='GET')
if resp:
    print(f"Cron response: {resp.read().decode('utf-8', errors='replace')[:200]}")
else:
    print("Cron FAILED")

print("\n=== DONE ===")

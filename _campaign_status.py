#!/usr/bin/env python3
"""Check campaign detail and emails sent"""
import urllib.request, json, ssl

PA_BASE = "https://jhfguf.pythonanywhere.com"
PA_TOKEN = "34fe3a4cafefe3a4ac8d592119d5480a0b988971"
USER = "JHFGUF"

ctx = ssl.create_default_context()

# Trigger another tick
print("Triggering tick #3 (last one for tonight)...")
try:
    req = urllib.request.Request(
        f"{PA_BASE}/api/cron/tick?reset=cooldown",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=300, context=ctx)
    result = json.loads(resp.read().decode())
    actions = result.get("actions", [])
    sent = result.get("sent", 0)
    print(f"Actions: {actions}")
    print(f"Sent in this tick: {sent}")
except Exception as e:
    print(f"Error: {e}")

# Check campaign via API - try to login
print(f"\nTrying to login and check campaign...")
try:
    # Login to get session
    import http.cookiejar, urllib.parse
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]
    
    data = urllib.parse.urlencode({
        "email": "samatou683@gmail.com",
        "password": "Admin@2026!"
    }).encode()
    req = urllib.request.Request(f"{PA_BASE}/login", data=data)
    resp = opener.open(req, timeout=15, context=ctx)
    
    # Check if login worked by trying dashboard
    req2 = urllib.request.Request(f"{PA_BASE}/dashboard")
    resp2 = opener.open(req2, timeout=15, context=ctx)
    body = resp2.read().decode("utf-8", errors="replace")
    
    if "login" in body[:500].lower():
        print("Login failed (redirected to login)")
    else:
        print("Login successful!")
        # Try campaign detail
        req3 = urllib.request.Request(f"{PA_BASE}/campaign/camp_bda44c26118f")
        resp3 = opener.open(req3, timeout=15, context=ctx)
        body3 = resp3.read().decode("utf-8", errors="replace")
        print(f"Campaign page loaded ({len(body3)} chars)")
        # Extract key stats
        import re
        for pattern in [r"sent[^<]*?\d+", r"total[^<]*?\d+", r"status[^<]*?\w+", r"email[^<]*?\w+"]:
            matches = re.findall(pattern, body3, re.I)
            for m in matches:
                print(f"  Found: {m}")
except Exception as e:
    print(f"Error: {e}")

# Final summary
print("\n=== SUMMARY ===")
try:
    req = urllib.request.Request(
        f"{PA_BASE}/api/dashboard/stats",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    print(f"Stats: {resp.read().decode()}")
except Exception as e:
    print(f"Error: {e}")

#!/usr/bin/env python3
"""Test PA login properly"""
import urllib.request, urllib.parse, http.cookiejar, re, sys

PA = "https://jhfguf.pythonanywhere.com"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler()
)
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0')]

# Try login
print("=== TRYING LOGIN ===")
data = urllib.parse.urlencode({
    'email': 'samatou683@gmail.com',
    'password': 'JobHunt4Pro#'
}).encode()
req = urllib.request.Request(f"{PA}/login", data=data, method='POST')
try:
    resp = opener.open(req, timeout=20)
    body = resp.read().decode('utf-8', errors='replace')
    print(f"Status: {resp.status}")
    
    # Print cookies
    print("\nCookies:")
    for c in cj:
        print(f"  {c.name} = {c.value[:50]}")
    
    # Check if login was successful (should say "invalid" if failed)
    if 'invalid' in body.lower() or 'incorrect' in body.lower() or 'error' in body.lower():
        print("\nLOGIN FAILED - checking for error message...")
        err_match = re.search(r'(?:error|alert|message|invalid)[^<]{0,100}', body, re.I)
        if err_match:
            print(f"Error: {err_match.group(0)}")
        # Check body for clues
        print(f"\nBody (first 2000 chars): {body[:2000]}")
    else:
        print("\nLOGIN LOOKS OK - checking pages...")
        
        # Try dashboard
        print("\n=== DASHBOARD ===")
        req2 = urllib.request.Request(f"{PA}/dashboard")
        resp2 = opener.open(req2, timeout=20)
        body2 = resp2.read().decode('utf-8', errors='replace')
        
        if 'login' in body2[:100].lower():
            print("Redirected to login - not authenticated")
            print(body2[:300])
        else:
            print("Dashboard accessed! Checking content...")
            print(f"Length: {len(body2)}")
            # Look for user info
            for pattern in [r'Sam', r'samatou', r'wallet', r'balance', r'campaign', r'profile']:
                matches = re.findall(pattern, body2, re.I)
                if matches:
                    print(f"Found '{pattern}': {len(matches)} matches")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"Error: {e}")

#!/usr/bin/env python3
"""
Debug PA login using the auto-renew script approach.
Try with URL-encoding the password.
"""
import requests, re, sys
from urllib.parse import quote

PASSWORD = "4HsJZvtwxz0fkfy%$*&$U58YFU"

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# Step 1: GET login page
r = s.get('https://www.pythonanywhere.com/login/', timeout=15)
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not csrf:
    print("NO CSRF!")
    sys.exit(1)

csrf_token = csrf.group(1)
print(f"CSRF: {csrf_token[:20]}...")

# Step 2: POST login - exactly like auto-renew script
r = s.post('https://www.pythonanywhere.com/login/', data={
    'csrfmiddlewaretoken': csrf_token,
    'auth-username': 'jhfguf',
    'auth-password': PASSWORD.encode('utf-8'),
    'login_view-current_step': 'auth',
}, headers={'Referer': 'https://www.pythonanywhere.com/login/'}, timeout=15)

print(f"Login status: {r.status_code}")
print(f"Login URL: {r.url}")
print(f"Login length: {len(r.text)}")

if 'Invalid' in r.text:
    print("INVALID LOGIN!")
    # Check the login page to see if there's an error message
    err = re.search(r'class="errorlist"[^>]*>([^<]+)', r.text)
    if err:
        print(f"Error: {err.group(1)}")
else:
    print("Login OK - no 'Invalid' found")
    
    # Try to access webapps
    r2 = s.get('https://www.pythonanywhere.com/user/jhfguf/webapps/', timeout=15)
    print(f"Webapps: {r2.status_code} {len(r2.text)}chars")
    if 'jhfguf.pythonanywhere.com' in r2.text:
        print("Found domain! Logged in successfully!")
        
        # Find reload
        reload_match = re.search(r'/user/jhfguf/webapps/([^/]+/reload)', r2.text)
        if reload_match:
            url = f"https://www.pythonanywhere.com/user/jhfguf/webapps/{reload_match.group(1)}"
            csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r2.text)
            if csrf2:
                r3 = s.post(url, data={'csrfmiddlewaretoken': csrf2.group(1)},
                    headers={'Referer': r2.url}, timeout=30)
                print(f"Reload: {r3.status_code} -> {'OK' if r3.status_code in (200,302) else r3.text[:100]}")
        else:
            # Print area around domain reference
            idx = r2.text.find('jhfguf.pythonanywhere.com')
            print(f"Found at {idx}: ...{r2.text[max(0,idx-100):idx+300]}...")
    else:
        print("No domain found")
        # Find next url or redirect
        next_match = re.search(r'name="next" value="([^"]*)"', r2.text)
        if next_match:
            print(f"Next URL field: {next_match.group(1)}")

#!/usr/bin/env python3
"""Reload PA web app via web login."""
import requests, re, sys
PASSWORD = "4HsJZvtwxz0fkfy%$*&$U58YFU"

s = requests.Session()
r = s.get('https://www.pythonanywhere.com/login/', timeout=15)
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not csrf:
    print("No CSRF")
    sys.exit(1)

r = s.post('https://www.pythonanywhere.com/login/', data={
    'csrfmiddlewaretoken': csrf.group(1),
    'auth-username': 'jhfguf',
    'auth-password': PASSWORD,
    'login_view-current_step': 'auth',
}, headers={'Referer': 'https://www.pythonanywhere.com/login/'}, timeout=15)

if 'Invalid' in r.text:
    print("Login FAILED!")
    sys.exit(1)
print("Login OK")

# Go to webapps page, find reload URL
r2 = s.get('https://www.pythonanywhere.com/user/jhfguf/webapps/', timeout=15)
print("Webapps page:", r2.status_code, len(r2.text))

# Find reload URL
reload_match = re.search(r'href="([^"]*reload[^"]*)"', r2.text)
if reload_match:
    url = reload_match.group(1)
    if url.startswith('/'):
        url = 'https://www.pythonanywhere.com' + url
    print("Reload URL:", url)
    
    # Also find CSRF
    csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r2.text)
    if csrf2:
        r3 = s.post(url, data={'csrfmiddlewaretoken': csrf2.group(1)},
            headers={'Referer': 'https://www.pythonanywhere.com/user/jhfguf/webapps/'},
            timeout=30)
        print("Reload:", r3.status_code)
        if r3.status_code in (200, 302):
            print("SUCCESS!")
        else:
            print(r3.text[:200])
    else:
        print("No CSRF on webapps page")
else:
    print("No reload link found")
    print(r2.text[:1000])

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

# Reload
r2 = s.post('https://www.pythonanywhere.com/user/jhfguf/webapps/jhfguf.pythonanywhere.com/reload/',
    data={'csrfmiddlewaretoken': csrf.group(1)},
    headers={'Referer': 'https://www.pythonanywhere.com/user/jhfguf/webapps/'},
    timeout=30)
print("Reload:", r2.status_code)
if r2.status_code in (200, 302):
    print("PA Reloaded!")
else:
    print(r2.text[:200])

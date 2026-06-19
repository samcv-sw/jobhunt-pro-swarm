#!/usr/bin/env python3
"""Reload PA web app with proper session handling."""
import requests, re, sys
PASSWORD = "4HsJZvtwxz0fkfy%$*&$U58YFU"

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# Get login page + CSRF
r = s.get('https://www.pythonanywhere.com/login/', timeout=15)
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not csrf:
    print("No CSRF on login page!")
    sys.exit(1)

# Login with proper form data
r = s.post('https://www.pythonanywhere.com/login/', data={
    'csrfmiddlewaretoken': csrf.group(1),
    'auth-username': 'jhfguf',
    'auth-password': PASSWORD,
    'login_view-current_step': 'auth',
    'next': '/user/jhfguf/webapps/',
}, headers={'Referer': 'https://www.pythonanywhere.com/login/'}, timeout=15, allow_redirects=True)

print("Login response:", r.status_code, len(r.text), "chars")
if "Invalid" in r.text:
    print("LOGIN FAILED!")
    sys.exit(1)

# Check where we are
if 'webapps' in r.url or 'webapps' in r.text:
    print("On webapps page!")
else:
    print(f"On page: {r.url}")
    print(f"Title: {re.search(r'<title>([^<]+)', r.text).group(1) if re.search(r'<title>([^<]+)', r.text) else 'unknown'}")
    
    # Try getting webapps directly
    r = s.get('https://www.pythonanywhere.com/user/jhfguf/webapps/', timeout=15)
    print("Webapps direct:", r.status_code, len(r.text), "chars")
    if 'Invalid' in r.text or 'Login' in r.text[:200]:
        print("Not authenticated!")
        sys.exit(1)

# Find reload link
reload_match = re.search(r'<a[^>]*href="([^"]*reload[^"]*)"[^>]*>', r.text, re.IGNORECASE)
if not reload_match:
    reload_match = re.search(r'form[^>]*action="([^"]*reload[^"]*)"', r.text, re.IGNORECASE)
if not reload_match:
    reload_match = re.search(r'/user/jhfguf/webapps/jhfguf\.pythonanywhere\.com/reload/', r.text)

if reload_match:
    url = reload_match.group(0).replace('action="', '').replace('href="', '').rstrip('"')
    if url.startswith('/'):
        url = 'https://www.pythonanywhere.com' + url
    print(f"Found: {url}")
    
    # Get CSRF
    csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
    if csrf2:
        r3 = s.post(url, data={'csrfmiddlewaretoken': csrf2.group(1)},
            headers={'Referer': r.url}, timeout=30)
        print("Reload:", r3.status_code)
        if r3.status_code in (200, 302):
            print("SUCCESS! PA reloaded!")
        else:
            print(r3.text[:300])
    else:
        print("No CSRF2")
else:
    print("No reload link found in webapps page")
    # Show the webapps page content around where reload might be
    idx = r.text.find('jhfguf.pythonanywhere.com')
    if idx >= 0:
        print(f"Found domain at {idx}: ...{r.text[max(0,idx-200):idx+200]}...")
    else:
        print("Domain not found either. Page excerpt:")
        print(r.text[:2000])

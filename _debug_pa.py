"""Debug PA file API path"""
import requests

TOKEN = '34fe3a4cafefe3a4ac8d592119d5480a0b988971'
USER = 'JHFGUF'
DOMAIN = 'jhfguf.pythonanywhere.com'
BASE = f'https://www.pythonanywhere.com/api/v0/user/{USER}'
h = {'Authorization': f'Token {TOKEN}'}

# Try different file API path formats
paths_to_try = [
    f'{BASE}/files/?path=/home/{USER}/jobhunt',
    f'{BASE}/files/path/home/{USER}/jobhunt',
    f'{BASE}/files/home/{USER}/jobhunt/config.py',
]

for url in paths_to_try:
    r = requests.get(url, headers=h)
    print(f'{r.status_code} GET {url.replace(BASE, "")}')
    if r.status_code == 200:
        print(f'  {r.text[:300]}')

# Also test reload with different method
reload_urls = [
    (f'{BASE}/webapps/{DOMAIN}/reload/', 'POST'),
    (f'{BASE}/webapps/{DOMAIN}/reload', 'PATCH'),
]
for url, method in reload_urls:
    if method == 'POST':
        r = requests.post(url, headers=h)
    else:
        r = requests.patch(url, headers=h)
    print(f'{r.status_code} {method} {url.replace(BASE, "")}')

# Get webapp details to find webapp ID
r = requests.get(f'{BASE}/webapps/', headers=h)
if r.status_code == 200:
    import json
    webapps = r.json()
    for w in webapps:
        print(f'\nWebapp ID: {w.get("id")}, domain: {w.get("domain_name")}')
        # Try reload with webapp ID
        wid = w.get('id')
        rr = requests.post(f'{BASE}/webapps/{wid}/reload/', headers=h)
        print(f'Reload by ID {wid}: {rr.status_code}')

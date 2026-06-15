"""Final verification - check login page and full audit"""
import requests

import os
PA = os.environ.get('TEST_URL', 'http://127.0.0.1:8000')

# Check login page for navbar
h = requests.get(PA + '/login', timeout=10).text
print('=== LOGIN PAGE CHECK ===')
for c in ['<div class="headroom">', 'class="brand"', '>Home<', '>Services<', '>Login<']:
    print(f'  {c:35s}: {"YES" if c in h else "NO"}')

# Full audit
print('\n=== FULL AUDIT ===')
s = requests.Session()
s.post(PA + '/login', data={'email': 'test_audit_64668@temp.com', 'password': 'TestPass123!'},
       headers={'Origin': PA, 'Referer': PA + '/login'}, allow_redirects=False, timeout=10)

all_pages = ['/', '/login', '/register', '/pricing', '/services', '/contact',
             '/faq', '/blog', '/referral', '/for-employers',
             '/user-dashboard', '/stats', '/wallet', '/battle-station',
             '/new-campaign', '/upload-cv', '/sent-emails',
             '/funnel-analytics', '/ats-scorer', '/resume-tailor',
             '/employers', '/email-test']

errors = []
for p in all_pages:
    resp = s.get(PA + p, timeout=10, allow_redirects=False)
    h = resp.text
    problems = []
    if resp.status_code != 200:
        problems.append(f'HTTP_{resp.status_code}')
    if 'cyberpunk.css' not in h:
        problems.append('NO_CYBER')
    if p in ['/user-dashboard', '/email-test', '/stats', '/wallet', '/battle-station',
             '/new-campaign', '/upload-cv', '/sent-emails', '/funnel-analytics',
             '/ats-scorer', '/resume-tailor', '/employers']:
        if 'class="sidebar"' not in h:
            problems.append('NO_SIDEBAR')
    if h.count('!DOCTYPE') > 1:
        problems.append('NESTED!')
    
    status = 'OK' if not problems else ' | '.join(problems)
    print(f'  {p:25s} {resp.status_code} {len(h):>6}b {status}')
    if problems:
        errors.append(f'{p}: {status}')

print(f'\n=== RESULT: {len(errors)} issues remaining ===')
if errors:
    for e in errors:
        print(f'  ! {e}')

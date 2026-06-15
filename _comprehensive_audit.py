"""Full auth audit with live session"""
import requests

PA = 'https://jhfguf.pythonanywhere.com'
s = requests.Session()

# Load saved account
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\session_info.txt') as f:
    lines = f.readlines()
email = lines[0].split(': ', 1)[1].strip()
pw = lines[1].split(': ', 1)[1].strip()

# Login
headers = {'Origin': PA, 'Referer': PA + '/login'}
s.get(PA + '/login', timeout=10)
r = s.post(PA + '/login', data={'email': email, 'password': pw},
           headers=headers, allow_redirects=False, timeout=10)
if r.status_code in (302, 303):
    s.get(PA + r.headers.get('Location', '/dashboard'), timeout=10)
print(f'Logged in as: {email}')

# All pages to check
ALL_PAGES = [
    '/user-dashboard', '/stats', '/wallet', '/battle-station',
    '/new-campaign', '/upload-cv', '/sent-emails',
    '/funnel-analytics', '/ats-scorer', '/resume-tailor',
    '/employers', '/email-test', '/export', '/antigravity',
    '/redeem', '/services', '/services/purchase', '/contact',
    '/referral', '/track-application', '/terms', '/trust',
    '/faq', '/blog', '/privacy', '/forgot-password',
    '/reset-password', '/login', '/register',
    '/pricing', '/checkout', '/premium',
    '/for-employers', '/employer/track',
    '/services/new', '/services-v2',
    '/war-room', '/about',
    '/unsubscribe',
    '/admin', '/admin-force-reset',
]

print(f'\n{"Page":35s} {"Status":6s} {"Size":8s} {"D":3s} {"C":3s} {"S":3s} {"T":3s} {"Notes"}')
print('-' * 100)

results = []
for path in ALL_PAGES:
    try:
        r = s.get(PA + path, timeout=15, allow_redirects=False)
        h = r.text if r.status_code == 200 else ''
        sz = len(h) if r.status_code == 200 else 0
        d = '<!DOCTYPE' in h[:200]
        c = 'cyberpunk.css' in h
        sb = 'dash-sidebar' in h or 'sidebar' in h[:5000].lower()
        ti = ''
        if '<title>' in h:
            ti = h[h.find('<title>')+7:h.find('</title>')][:25]
        
        notes = ''
        if r.status_code == 303:
            notes = f'->{r.headers.get("Location","?")[:30]}'
        elif d and not c:
            notes = 'NO_CYBER'
        elif d and not sb and path.startswith('/user'):
            notes = 'NO_SIDEBAR'
        elif 'login' in h[:1000].lower() and path != '/login':
            notes = 'ON_LOGIN_PAGE'
        elif sz < 100:
            notes = 'TOO_SMALL'
        
        status = str(r.status_code)
        status_str = f'{status:>5s}' if r.status_code == 200 else f' {status}'
        
        results.append((path, r.status_code, sz, d, c, sb, ti, notes))
        print(f'{path:35s} {status_str:6s} {str(sz):>8s} {"Y" if d else "N":3s} {"Y" if c else "N":3s} {"Y" if sb else "N":3s} {"Y" if ti else "N":3s} {notes}')
    except Exception as e:
        print(f'{path:35s} {"ERROR":>6s} {"":>8s}   {str(e)[:50]}')

# Summary
print(f'\n=== SUMMARY ===')
print(f'Pages checked: {len(results)}')
cyber_missing = [p for p in results if p[1] == 200 and not p[4]]
print(f'Missing cyberpunk.css: {len(cyber_missing)}')
for p in cyber_missing:
    print(f'  {p[0]}')

sidebar_missing = [p for p in results if p[1] == 200 and p[0].startswith('/user') and not p[5]]
print(f'\nAuth pages missing sidebar: {len(sidebar_missing)}')
for p in sidebar_missing:
    print(f'  {p[0]}')

redirect_pages = [p for p in results if p[1] in (301, 302, 303)]
print(f'\nRedirect pages: {len(redirect_pages)}')
for p in redirect_pages:
    print(f'  {p[0]} -> (HTTP {p[1]})')

small_pages = [p for p in results if p[1] == 200 and p[2] < 500]
print(f'\nSmall pages (<500 bytes): {len(small_pages)}')
for p in small_pages:
    print(f'  {p[0]} ({p[2]} bytes)')

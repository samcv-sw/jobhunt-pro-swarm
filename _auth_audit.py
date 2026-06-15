"""Login + audit ALL pages including auth pages"""
import urllib.request, urllib.parse, re, json

PA = 'https://jhfguf.pythonanywhere.com'

# 1. Login
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
urllib.request.install_opener(opener)

login_data = urllib.parse.urlencode({'username': 'testqclaw456@example.com', 'password': 'testpass123!'}).encode()
resp = urllib.request.urlopen(PA + '/login', data=login_data, timeout=15)
print(f'Login: {resp.status} {resp.reason}')

# 2. Check auth pages
AUTH_PAGES = [
    '/user-dashboard', '/stats', '/wallet', '/battle-station', 
    '/new-campaign', '/upload-cv', '/sent-emails',
    '/funnel-analytics', '/ats-scorer', '/resume-tailor',
    '/employers', '/redeem', '/email-test', '/export',
    '/antigravity', '/campaign/12345',
]

print(f'\n{"Page":30s} {"Size":8s} DOCTYPE Cyber Side Notes')
print('-' * 80)
for path in AUTH_PAGES:
    try:
        resp = urllib.request.urlopen(PA + path, timeout=15)
        html = resp.read().decode('utf-8', errors='replace')
        sz = len(html)
        d = '<!DOCTYPE' in html[:100]
        c = 'cyberpunk.css' in html
        s = 'class="sidebar"' in html or 'class="dash-sidebar"' in html
        nav = 'sidebar' in html.lower()
        # Grab context
        notes = ''
        first = html[:100].strip()[:60]
        if 'login' in html[:1000].lower():
            notes = 'REDIRECTED TO LOGIN'
        elif not d:
            notes = f'NO_DOCTYPE first={first}'
        print(f'{path:30s} {sz:>8} {d} {c} {s} {notes}')
    except urllib.error.HTTPError as e:
        print(f'{path:30s} {"":>8} {"HTTP":7s} {e.code} {e.reason}')
    except Exception as e:
        print(f'{path:30s} {"":>8} {str(e)[:60]}')

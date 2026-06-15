"""Check specific pages that might need fixing"""
import requests

s = requests.Session()
PA = 'https://jhfguf.pythonanywhere.com'
headers = {'Origin': PA, 'Referer': PA + '/login'}
s.get(PA + '/login', timeout=10)
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\session_info.txt') as f:
    email = f.readline().split(': ', 1)[1].strip()
    pw = f.readline().split(': ', 1)[1].strip()
r = s.post(PA + '/login', data={'email': email, 'password': pw}, headers=headers, allow_redirects=False, timeout=10)
s.get(PA + '/dashboard', timeout=10)

# Check pages that may be broken
for path in ['/unsubscribe', '/admin-force-reset', '/login', '/register', '/forgot-password',
             '/contact', '/faq', '/blog', '/services', '/employer/track',
             '/pricing', '/checkout', '/referral', '/services/new']:
    try:
        r = s.get(PA + path, timeout=10, allow_redirects=True)
        h = r.text
        d = '<!DOCTYPE' in h[:200]
        c = 'cyberpunk.css' in h
        sb = 'dash-sidebar' in h or 'sidebar' in h
        nav = 'nav' in h[:2000].lower()
        body_start = h.find('<body')
        body_content = h[body_start:body_start+500] if body_start >= 0 else ''
        has_nav_in_body = 'nav' in body_content.lower() or 'navbar' in body_content.lower()
        title = h[h.find('<title>')+7:h.find('</title>')][:30] if '<title>' in h else 'NO_TITLE'
        print(f'\n=== {path} ===')
        print(f'  Size: {len(h)} | DOCTYPE: {d} | Cyber: {c} | Sidebar: {sb} | Nav: {nav} | BodyNav: {has_nav_in_body}')
        print(f'  Title: {title}')
        print(f'  First: {h[:120]}')
    except Exception as e:
        print(f'{path}: ERROR {e}')

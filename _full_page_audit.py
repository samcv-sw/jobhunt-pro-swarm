"""Full page audit - check every page for issues"""
import urllib.request, http.cookiejar, io, gzip, re

BASE = 'https://jhfguf.pythonanywhere.com'

# Login as test user
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(BASE + '/login')
data = 'email=testqclaw456@example.com&password=Test1234!'.encode()
req = urllib.request.Request(BASE + '/login', data=data, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
req.add_header('Origin', BASE)
req.add_header('Referer', BASE + '/login')
opener.open(req)

def fetch(url):
    try:
        resp = opener.open(url, timeout=10)
        html = resp.read().decode('utf-8', errors='replace')
        return resp.getcode(), html
    except urllib.request.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)

def check_page(name, url):
    status, html = fetch(url)
    issues = []
    
    if status != 200:
        return f'{name:25s} | {status:3d} ❌ ERROR'
    
    # Check for errors
    if len(html) < 200:
        issues.append('EMPTY')
    
    # Page structure
    has_dash_sidebar = '<div class="dash-sidebar">' in html
    has_shell_sidebar = 'class="sidebar"' in html and '<nav>' in html
    has_dash_main = 'class="dash-main"' in html
    has_cyberpunk = 'cyberpunk.css' in html
    has_body = '<body' in html
    has_doctype = '<!DOCTYPE' in html
    has_traceback = 'Traceback' in html
    
    if has_traceback:
        issues.append('TRACEBACK')
    
    pages_sidebar = has_dash_sidebar or has_shell_sidebar
    
    return f'{name:25s} | {status:3d} size={len(html):>6} sidebar={1 if pages_sidebar else 0} cyber={1 if has_cyberpunk else 0}' + (f' | ⚠️  {", ".join(issues)}' if issues else '')

print('=== PUBLIC PAGES (no login needed) ===')
for path in ['/', '/login', '/register', '/pricing', '/services', '/contact', '/referral',
             '/for-employers', '/trust', '/forgot-password', '/war-room']:
    url = BASE + path if path != 'N/A' else None
    if url:
        print(check_page(path, url))

print()
print('=== AUTH PAGES (logged in as test user) ===')
for path in ['/user-dashboard', '/new-campaign', '/upload-cv', '/wallet', '/stats',
             '/sent-emails', '/battle-station', '/funnel-analytics', '/ats-scorer', '/resume-tailor']:
    print(check_page(path, BASE + path))

print()
print('=== SPECIAL ROUTES ===')
print(check_page('health', BASE + '/health'))
print(check_page('cron/tick', BASE + '/api/cron/tick'))

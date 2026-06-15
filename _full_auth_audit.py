"""Full page audit - check ALL pages for sidebar status"""
import urllib.request, http.cookiejar

base = 'https://jhfguf.pythonanywhere.com'

# Login
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(base + '/login')
data = b'email=testqclaw456@example.com&password=Test1234!'
req = urllib.request.Request(base + '/login', data=data, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
req.add_header('Origin', base)
opener.open(req)

# ALL auth pages that should have sidebar
pages = [
    ('/user-dashboard', 'Dashboard'),
    ('/stats', 'Stats'),
    ('/wallet', 'Wallet'),
    ('/battle-station', 'Battle Station'),
    ('/sent-emails', 'Sent Emails'),
    ('/new-campaign', 'New Campaign'),
    ('/upload-cv', 'Upload CV'),
    ('/funnel-analytics', 'Funnel Analytics'),
    ('/ats-scorer', 'ATS Scorer'),
    ('/resume-tailor', 'Resume Tailor'),
]

for path, name in pages:
    try:
        resp = opener.open(base + path, timeout=10)
        html = resp.read().decode('utf-8', errors='replace')
        h = 'class="sidebar"' in html
        d = 'class="dash-sidebar"' in html
        c = 'cyberpunk.css' in html
        has_sb = h or d
        status = 'OK' if has_sb else 'MISSING SIDEBAR'
        sign = '*' if not has_sb else ' '
        print(f'{sign} {name:20s} ({path:20s}) sidebar={h} dash={d} cyber={c} -> {status}')
    except Exception as e:
        print(f'  {name:20s} ({path:20s}) ERROR: {e}')

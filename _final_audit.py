"""Final full audit"""
import requests

PA = 'https://jhfguf.pythonanywhere.com'
s = requests.Session()

# Login
s.post(PA + '/login', data={'email': 'test_audit_64668@temp.com', 'password': 'TestPass123!'},
       headers={'Origin': PA, 'Referer': PA + '/login'}, allow_redirects=False, timeout=10)

pages = [
    ('/', 'public'),
    ('/login', 'public'),
    ('/register', 'public'),
    ('/pricing', 'public'),
    ('/services', 'public'),
    ('/contact', 'public'),
    ('/faq', 'public'),
    ('/blog', 'public'),
    ('/referral', 'public'),
    ('/for-employers', 'public'),
    ('/user-dashboard', 'auth'),
    ('/stats', 'auth'),
    ('/wallet', 'auth'),
    ('/battle-station', 'auth'),
    ('/new-campaign', 'auth'),
    ('/upload-cv', 'auth'),
    ('/sent-emails', 'auth'),
    ('/funnel-analytics', 'auth'),
    ('/ats-scorer', 'auth'),
    ('/resume-tailor', 'auth'),
    ('/employers', 'auth'),
    ('/email-test', 'auth'),
]

all_ok = True
for p, ptype in pages:
    try:
        resp = s.get(PA + p, timeout=10, allow_redirects=False)
        h = resp.text
        status = resp.status_code
        
        issues = []
        if status != 200:
            issues.append(f'STATUS={status}')
        
        # Check cyberpunk
        if 'cyberpunk.css' not in h:
            issues.append('NO_CYBER')
        
        # Check navbar (public pages) or sidebar (auth pages)
        if ptype == 'public' and 'headroom' not in h[:2000]:
            # Login/register might have it differently
            if 'brand' not in h[:1000]:
                issues.append('NO_NAV')
        
        if ptype == 'auth':
            if 'class="sidebar"' not in h and 'class="dash-sidebar"' not in h:
                issues.append('NO_SIDEBAR')
        
        # Check nesting
        if h.count('!DOCTYPE') > 1:
            issues.append('NESTED_DOCTYPE')
        
        notes = ' | '.join(issues) if issues else 'OK'
        icon = '  ' if not issues else '!!'
        print(f'{p:25s} {status:3d} {len(h):>6}b {icon} {notes}')
        if issues and p != '/login' and p != '/register':
            all_ok = False
    except Exception as e:
        print(f'{p:25s} ERROR: {str(e)[:60]}')
        all_ok = False

print(f'\nAll pages OK: {all_ok}')

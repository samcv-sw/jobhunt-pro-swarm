"""Full route audit - ALL pages + sidebar status"""
import urllib.request, http.cookiejar
import re

base = 'https://jhfguf.pythonanywhere.com'
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(base + '/login')
d = b'email=testqclaw456@example.com&password=Test1234!'
r = urllib.request.Request(base + '/login', data=d, method='POST')
r.add_header('Content-Type', 'application/x-www-form-urlencoded')
r.add_header('Origin', base)
opener.open(r)

# ALL potential routes to check
all_routes = [
    '/user-dashboard', '/stats', '/wallet', '/battle-station', '/sent-emails',
    '/new-campaign', '/upload-cv', '/funnel-analytics', '/ats-scorer',
    '/resume-tailor', '/contact', '/faq', '/about', '/settings',
    '/track-application', '/services', '/services-new',
    '/services-v2', '/referral', '/api-docs', '/checkout',
    '/checkout-v2', '/pricing', '/war-room', '/for-employers',
    '/employer-track', '/subscription', '/notifications',
    '/campaigns', '/applications', '/analytics',
]

print(f'{"ROUTE":25s} {"STATUS":8s} {"SIZE":8s} {"SB":4s} {"CYBER":6s}')
print('-' * 55)

ok, missing_sb, err_count = 0, 0, 0
missing_list = []

for path in all_routes:
    try:
        resp = opener.open(base + path, timeout=10)
        html = resp.read().decode('utf-8', errors='replace')
        code = resp.getcode()
        h = 'class="sidebar"' in html
        d = 'dash-sidebar' in html
        c = 'cyberpunk.css' in html
        has_sb = h or d
        
        print(f'{path:25s} {code:<8} {len(html):<8} {str(has_sb):4} {str(c):6}')
        
        if code == 200 and not has_sb:
            missing_sb += 1
            missing_list.append(path)
        if code == 200:
            ok += 1
    except urllib.request.HTTPError as e:
        print(f'{path:25s} {e.code:<8} {"-":8} {"-":4} {"-":6}')
        if e.code != 303:
            err_count += 1
    except Exception as e:
        print(f'{path:25s} {"ERR":8} {"-":8} {"-":4} {"-":6}')
        err_count += 1

print(f'\nOK={ok} Missing Sidebar={missing_sb} Errors={err_count}')
if missing_list:
    print(f'\nPages WITHOUT sidebar:')
    for p in missing_list:
        print(f'  ❌ {p}')

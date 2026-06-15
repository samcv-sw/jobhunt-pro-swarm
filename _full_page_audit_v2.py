"""AUDIT: ALL pages on JobHunt Pro"""
import urllib.request, urllib.error, re, json

BASE = 'https://jhfguf.pythonanywhere.com'
PA_TOKEN = '7e7ad272cc2d4470e8078fca29dfacf301fb01fe'

# First: extract ALL routes from app_v2.py
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py', 'rb') as f:
    code = f.read().decode('utf-8', errors='replace')

lines = code.split('\n')
ALL_ROUTES = []
for i, line in enumerate(lines):
    m = re.match(r'@app\.(get|post)\("([^"]+)"', line.strip())
    if m:
        method, path = m.group(1), m.group(2)
        # Find the function name (next few lines)
        func_name = ''
        for j in range(i+1, min(i+5, len(lines))):
            fm = re.match(r'(async def|def) (\w+)', lines[j].strip())
            if fm:
                func_name = fm.group(2)
                break
        
        # Check if it renders HTML or returns JSON/redirect
        func_lines = []
        for j in range(i, min(i+60, len(lines))):
            func_lines.append(lines[j])
            if j > i and lines[j].strip().startswith(('@app.', 'async def', 'def ', '')) and j > i+1:
                if not lines[j].strip().startswith(('@app.', 'async def', 'def ')):
                    continue
                break
        func_text = '\n'.join(func_lines)
        
        has_auth = 'get_verified_user_id' in func_text
        has_shell = '_build_dashboard_shell' in func_text
        has_public = '_public_shell' in func_text
        has_template = 'TemplateResponse' in func_text
        has_html = 'HTMLResponse' in func_text
        has_redirect = 'RedirectResponse' in func_text
        has_render = 'render_template' in func_text
        is_post = 'req=None' in func_text or 'Form(' in func_text or method == 'post'
        
        ALL_ROUTES.append({
            'method': method.upper(),
            'path': path,
            'func': func_name,
            'auth': has_auth,
            'shell': has_shell,
            'public': has_public,
            'template': has_template,
            'html': has_html,
            'redirect': has_redirect,
            'render': has_render,
            'is_post': is_post,
        })

# Filter: only GET routes that render HTML pages (not API, not static, not redirect-only)
RENDER_ROUTES = [r for r in ALL_ROUTES if r['method'] == 'GET' and not r['path'].startswith(('/api/', '/static/', '/webhook/', '/cron/')) and not r['path'].startswith('/admin/') and not r['is_post']]

print(f"Total routes: {len(ALL_ROUTES)}")
print(f"GET render routes: {len(RENDER_ROUTES)}")
print()

# Test each route via HTTP
def test_page(path):
    """Returns (status, size, has_doctype, has_cyber, has_sidebar, issues_str)"""
    try:
        req = urllib.request.Request(BASE + path)
        req.add_header('User-Agent', 'Mozilla/5.0')
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read()
        status = resp.status
        
        if status >= 300 and status < 400:
            redirect = resp.headers.get('Location', '')
            return status, 0, False, False, False, f'Redirect→{redirect[:60]}'
        
        text = html.decode('utf-8', errors='replace')
        size = len(text)
        has_doctype = '<!DOCTYPE' in text
        has_cyber = 'cyberpunk.css' in text
        has_sidebar = 'class="sidebar"' in text or 'class="dash-sidebar"' in text
        has_navbar = 'navbar' in text.lower() or 'nav' in text[:200].lower()
        has_body = '<body' in text
        has_html_close = '</html>' in text
        
        issues = []
        if not has_doctype: issues.append('NO_DOCTYPE')
        if not has_body: issues.append('NO_BODY')
        if not has_html_close: issues.append('NO_HTML_END')
        
        return status, size, has_doctype, has_cyber, has_sidebar, '|'.join(issues)
    except urllib.error.HTTPError as e:
        return e.code, 0, False, False, False, f'HTTP {e.code}'
    except Exception as e:
        return 0, 0, False, False, False, f'ERR: {str(e)[:60]}'

results = []
for route in RENDER_ROUTES:
    path = route['path']
    # Skip param-based routes
    if '{' in path:
        continue
    status, size, doctype, cyber, sidebar, issues = test_page(path)
    route['status'] = status
    route['size'] = size
    route['doctype'] = doctype
    route['cyber'] = cyber
    route['sidebar'] = sidebar
    route['issues'] = issues
    results.append(route)

# Print results sorted by status
print(f"{'Page':30s} {'Status':6s} {'Size':8s} {'DOCTYPE':8s} {'Cyber':8s} {'Sidebar':8s} {'Issues'}")
print('-' * 100)
for r in sorted(results, key=lambda x: (x['path'])):
    path = r['path']
    status = str(r['status'])
    size = str(r['size'])
    doctype = 'OK' if r['doctype'] else 'X'
    cyber = 'OK' if r['cyber'] else 'X'
    sidebar = 'OK' if r['sidebar'] else 'X'
    issues = r['issues']
    wrong_status = '' if r['status'] == 200 else f' httperror{r["status"]}'
    print(f'{path:30s} {status:6s} {size:8s} {doctype:8s} {cyber:8s} {sidebar:8s} {issues}{wrong_status}')

# Also test auth pages (need session cookie)
print()
print('=== AUTH PAGES (need login) ===')
# Try dashboard (will redirect to login)
try:
    req = urllib.request.Request(BASE + '/user-dashboard')
    req.add_header('User-Agent', 'Mozilla/5.0')
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')
    print(f'/user-dashboard: size={len(html)} doctype={":)" if "<!DOCTYPE" in html else "X"} cyber={"cyberpunk.css" in html}')
except urllib.error.HTTPError as e:
    location = e.headers.get('Location', 'n/a')
    print(f'/user-dashboard: HTTP {e.code} → {location}')

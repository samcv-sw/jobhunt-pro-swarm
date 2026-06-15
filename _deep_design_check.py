"""Detailed design checks on key pages"""
import requests

PA = 'https://jhfguf.pythonanywhere.com'
s = requests.Session()

# Check login page navbar actually renders (not just CSS)
for p, name in [('/login', 'Login'), ('/register', 'Register')]:
    resp = s.get(PA + p, timeout=10)
    h = resp.text
    print(f'=== {name} ({p}) ===')
    print(f'  Size: {len(h)}b')
    
    # Find the first <div class="headroom"> - the actual navbar div
    navbar_start = h.find('<div class="headroom">')
    if navbar_start > 0:
        # Find the </div> that closes it (3 divs deep: headroom > brand + nav)
        navbar_end = h.find('</nav>', navbar_start)
        if navbar_end > 0:
            navbar_end = h.find('</div>', navbar_end) + 6
        else:
            navbar_end = h.find('</div>', navbar_start) + 6
        
        print(f'  Navbar: YES (at pos {navbar_start})')
        print(f'  Navbar HTML: {h[navbar_start:navbar_end]}')
        print()
    else:
        print(f'  Navbar: NOT FOUND!')
        body_start = h.find('<body')  
        print(f'  After body: {h[body_start:body_start+200]}')
        print()

# Check homepage - does it have any broken images or missing elements
print('=== Homepage / ===')
resp = s.get(PA + '/', timeout=10)
h = resp.text
import re
imgs = re.findall(r'<img[^>]*src=([\'"])([^\'"]+)\1', h)
print(f'  Images: {len(imgs)}')
for src, _ in imgs[:5]:
    print(f'    {src}')
if len(imgs) > 5:
    print(f'    ... and {len(imgs)-5} more')

# Check for any placeholder/incomplete text
placeholders = re.findall(r'{%.*?%}', h)
if placeholders:
    print(f'  UNRENDERED JINJA2: {placeholders[:3]}')

# Check for double newlines or blank content
if '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' in h:
    print('  Has repeated nbsp')

print()

# Check auth dashboard for sidebar content
print('=== Dashboard /user-dashboard ===')
s.post(PA + '/login', data={'email': 'test_audit_64668@temp.com', 'password': 'TestPass123!'},
       headers={'Origin': PA, 'Referer': PA + '/login'}, allow_redirects=False, timeout=10)
resp = s.get(PA + '/user-dashboard', timeout=10)
h = resp.text
if 'class="sidebar"' in h:
    print(f'  Sidebar: YES')
    si = h.find('class="sidebar"')
    sb_end = h.find('</div>', si + 200) 
    print(f'  Sidebar HTML: {h[si-50:si+200][:250]}')
else:
    print(f'  Sidebar: NO')
print(f'  Main content starts at: {h[:200][:200]}')

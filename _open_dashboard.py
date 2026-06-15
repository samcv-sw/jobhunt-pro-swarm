"""Save the dashboard HTML to a file so we can open it in browser"""
import urllib.request, http.cookiejar

# Login
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# GET login page
opener.open('https://jhfguf.pythonanywhere.com/login')

# POST login
data = 'email=testqclaw456@example.com&password=Test1234!'.encode()
req = urllib.request.Request('https://jhfguf.pythonanywhere.com/login', data=data, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
req.add_header('Origin', 'https://jhfguf.pythonanywhere.com')
req.add_header('Referer', 'https://jhfguf.pythonanywhere.com/login')
resp = opener.open(req)

# Now get dashboard
resp2 = opener.open('https://jhfguf.pythonanywhere.com/user-dashboard')
html = resp2.read().decode('utf-8', errors='replace')

# Save to file
out = r'C:\Users\samde\Desktop\cv sam new ma3 kimi\_dashboard_preview.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

# Open in browser
import subprocess, os
os.startfile(out)

print(f'Saved: {len(html)} bytes')
print(f'Has dash-sidebar: {"dash-sidebar" in html}')
print(f'Has dash-main: {"dash-main" in html}')
print(f'Has sidebar element: {"<div class=\"dash-sidebar\">" in html}')

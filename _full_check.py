"""Full system check - what's deployed vs local"""
import subprocess, urllib.request

# 1. Git log
result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, cwd=r'C:\Users\samde\Desktop\cv sam new ma3 kimi')
print(f'GIT LOG:\n{result.stdout.decode()}')

# 2. Check app_v2.py route
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')
idx = content.find('async def user_dashboard')
section = content[idx:idx+10000]
return_idx = section.find('return ')
print(f'\nAPP_V2 DASHBOARD ROUTE return:\n{section[return_idx:return_idx+100]}')

# 3. Fetch PA dashboard HTML (check what's actually live)
print('\n=== PA LIVE DASHBOARD HTML (first 2000 chars) ===')
req = urllib.request.Request('https://jhfguf.pythonanywhere.com/user-dashboard')
try:
    resp = urllib.request.urlopen(req, timeout=10)
    html = resp.read().decode('utf-8', errors='replace')
    print(html[:2000])
except urllib.request.HTTPError as e:
    html = e.read().decode('utf-8', errors='replace')
    print(f'HTTP {e.code} - {html[:500]}')

"""Inspect shell templates and find the sidebar class"""
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates\_sidebar_head.html', 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

import re

# Find sidebar CSS class definition
m = re.search(r'\.sidebar\s*\{[^}]+', text)
print('=== Sidebar CSS in _sidebar_head.html ===')
if m:
    print(m.group()[:300])
else:
    print('NO sidebar CSS in _sidebar_head')

# Find sidebar HTML template
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates\_sidebar.html', 'rb') as f:
    sidebar = f.read().decode('utf-8', errors='replace')
print()
print('=== _sidebar.html (first 300 chars) ===')
print(sidebar[:300])

# Find _build_dashboard_shell in app_v2.py
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py', 'rb') as f:
    app = f.read().decode('utf-8', errors='replace')
idx = app.find('def _build_dashboard_shell')
if idx >= 0:
    end = app.find('\ndef ', idx + 50)
    print()
    print('=== _build_dashboard_shell ===')
    print(app[idx:end][:2000])

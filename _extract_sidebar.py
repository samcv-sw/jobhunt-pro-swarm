"""Extract sidebar HTML from _build_dashboard_shell and add to dashboard_v2.html."""
import re

# Read app_v2.py
with open('web/app_v2.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

# Find _build_dashboard_shell
idx = content.find('def _build_dashboard_shell')
shell = content[idx:idx+4000]

# Find sidebar div and content div start
sidebar_start = shell.find('<div class="sidebar"')
content_div_start = shell.find('<div class="content"')
sidebar_end = shell.find('</nav>', sidebar_start) + len('</nav>')

sidebar_html = shell[sidebar_start:sidebar_end]
# Fix the template expressions for newlines/indentation
sidebar_html = sidebar_html.replace('\\n', '\n').replace('    ', '')

print('=== SIDEBAR HTML ===')
print(sidebar_html[:1000])
print('...')
print(f'Length: {len(sidebar_html)}')

# Also get the CSS styles for the sidebar
style_start = shell.find('<style>', idx + 2000)
style_end = shell.find('</style>', style_start) + len('</style>')
sidebar_css = shell[style_start:style_end]
print('\n=== SIDEBAR CSS ===')
print(sidebar_css[:500])

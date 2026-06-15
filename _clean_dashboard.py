"""Clean dashboard_v2.html: remove all head-level tags, keep only CSS + content."""
import re

path = r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates\dashboard_v2.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

before = len(content)

# Remove <meta ... /> tags
content = re.sub(r'\s*<meta[^>]*/?>', '', content)
# Remove <title>...</title>
content = re.sub(r'\s*<title>[^<]*</title>', '', content)
# Remove <link ...> tags (font links)
content = re.sub(r'\s*<link[^>]*rel=["\']stylesheet["\'][^>]*>', '', content)
content = re.sub(r'\s*<link[^>]*>', '', content)
# Remove empty <script> tags and <noscript>
content = re.sub(r'\s*<script[^>]*>\s*</script>', '', content)
content = re.sub(r'\s*<noscript>[^<]*</noscript>', '', content)

# Remove extra blank lines at start
content = content.strip()

content = re.sub(r'\n{3,}', '\n\n', content)

after = len(content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Cleaned: {before} -> {after} chars ({before - after} removed)')
print(f'First 100 chars: {content[:100]}')

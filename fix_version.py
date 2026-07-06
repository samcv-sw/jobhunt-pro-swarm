import re

files = [
    'web/templates/_public_nav.html',
    'web/templates/en/_public_nav.html',
]

for path in files:
    try:
        content = open(path, encoding='utf-8', errors='ignore').read()
        # Remove hardcoded fallback defaults — let the template variable speak for itself
        fixed = content
        fixed = fixed.replace("VERSION|default('16.3')", "VERSION")
        fixed = fixed.replace('VERSION|default("16.3")', "VERSION")
        fixed = fixed.replace("VERSION|default('17')", "VERSION")
        fixed = fixed.replace("VERSION|default('17.0')", "VERSION")
        fixed = fixed.replace('VERSION|default("17.0")', "VERSION")
        if fixed != content:
            open(path, 'w', encoding='utf-8').write(fixed)
            print(f'Fixed: {path}')
        else:
            print(f'No change needed: {path}')
    except Exception as e:
        print(f'Error {path}: {e}')

# Check config.py VERSION value
cfg = open('config.py', encoding='utf-8', errors='ignore').read()
m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', cfg)
print(f'\nconfig.py VERSION = {m.group(1) if m else "NOT FOUND"}')

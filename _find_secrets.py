import re

with open('web/app_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find lines with hardcoded Google Client ID or Secret fallback
for m in re.finditer(
    r'GOOGLE_CLIENT_(ID|SECRET)\s*=.*os\.getenv\([^)]+\)\s*,\s*"([^"]+)"',
    content
):
    line_num = content[:m.start()].count('\n') + 1
    var_name = m.group(1)
    fallback_val = m.group(2)
    masked = fallback_val[:8] + '...' + fallback_val[-4:] if len(fallback_val) > 15 else fallback_val
    print(f"Line {line_num}: GOOGLE_CLIENT_{var_name} fallback = '{masked}' ({len(fallback_val)} chars)")

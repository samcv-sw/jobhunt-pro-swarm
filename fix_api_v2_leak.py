import re

p = 'web/routers/api_v2.py'
s = open(p, encoding='utf-8').read()

# Remove the client-facing exception detail leak inside campaign_stats_api
# Matches: "campaigns": {...},\n            "error": str(e)\n        }
pattern = re.compile(r'("campaigns": \{[^}]*\},\n)\s*"error": str\(e\)\n(\s*\})', re.DOTALL)
new_s, n = pattern.subn(r'\1\2', s)
assert n == 1, f'Expected exactly 1 replacement, got {n}'

open(p, 'w', encoding='utf-8').write(new_s)
print('FIXED_LEAK', n)

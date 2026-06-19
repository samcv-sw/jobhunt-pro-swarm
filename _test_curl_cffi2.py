"""Deep analysis of Bayt and Dice HTML"""
from curl_cffi import requests
import re, json

print("=== BAYT DEEP ===")
r = requests.get(
    "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/",
    impersonate="chrome120",
    timeout=15
)
html = r.text

# Find JSON-LD
ld_scripts = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', html)
print(f"JSON-LD scripts: {len(ld_scripts)}")
for i, script in enumerate(ld_scripts[:3]):
    try:
        j = json.loads(script)
        t = j.get('@type', '?')
        if isinstance(j, dict) and t == 'ItemList':
            items = j.get('itemListElement', [])
            print(f"  [{i}] ItemList with {len(items)} items")
            for item in items[:3]:
                it = item.get('item', item)
                if isinstance(it, dict):
                    print(f"    - {it.get('title','?')} @ {it.get('url','?')}")
        else:
            print(f"  [{i}] {t}: {json.dumps(j)[:200]}")
    except:
        snippet = script[:300].replace('\n',' ')
        print(f"  [{i}] PARSE FAIL: {snippet}")

# Find company/title patterns  
print("\n=== DICE DEEP ===")
r = requests.get(
    "https://www.dice.com/jobs?q=network+engineer",
    impersonate="chrome120",
    timeout=15
)
html = r.text

# Find job cards - look for data attributes
cards = re.findall(r'data-cy="search-card"[^>]*>([\s\S]*?)</a>', html)
print(f"'search-card' matches: {len(cards)}")

# Try various job title patterns
for pattern in ['jobTitle', 'card-title', 'job-title', 'position', 'title', 'role']:
    matches = re.findall(f'["\']\w*{pattern}\w*["\'][^>]*>([^<]+)', html, re.IGNORECASE)
    if matches:
        print(f"  '{pattern}': {len(matches)} matches - {matches[:3]}")

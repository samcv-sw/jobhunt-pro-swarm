"""Fix Bayt parser + test Dice with more selectors"""
from curl_cffi import requests
import re, json

print("=== BAYT - FULL ITEM STRUCTURE ===")
r = requests.get(
    "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/",
    impersonate="chrome120",
    timeout=15
)
# Full JSON-LD
ld_scripts = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', r.text)
j = json.loads(ld_scripts[0])
if j.get('@type') == 'ItemList':
    first = j['itemListElement'][0]
    it = first.get('item', first)
    print(f"First item keys: {list(it.keys())}")  
    print(f"First item full: {json.dumps(it, indent=2)[:600]}")

print("\n=== DICE DEEP v2 ===")
r2 = requests.get(
    "https://www.dice.com/jobs?q=network+engineer",
    impersonate="chrome120",
    timeout=15
)
html = r2.text

# Look for any h1-h4 with job-related text
titles = re.findall(r'<h[1-4][^>]*>([^<]*(?:engineer|network|admin|support)[^<]*)</h[1-4]>', html, re.IGNORECASE)
print(f"Engineer-related headings: {len(titles)}")
if titles: print(f"  Samples: {titles[:5]}")

# Look for data attributes
data_matches = re.findall(r'data-(?:testid|cy|automation|id)="([^"]*)"', html)
unique = list(set(data_matches))
print(f"Unique data attributes: {unique[:30]}")

# Any links with /job-detail/
links = re.findall(r'href="(/job-detail/[^"]*)"', html)
print(f"Job detail links: {len(links)}")
if links: print(f"  Samples: {links[:5]}")

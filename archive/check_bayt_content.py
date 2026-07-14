import json
import re

import cloudscraper

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True, 'mobile': False})
resp = scraper.get('https://www.bayt.com/en/international/jobs/', timeout=30)
html = resp.text

# Look for JSON-LD structured data
ld_json = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if ld_json:
    for j in ld_json[:2]:
        try:
            data = json.loads(j)
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        except:
            print(f"JSON-LD block: {j[:200]}")

# Look for job card elements
for pattern_name, pattern in [
    ("position-title", r'class="[^"]*position-title[^"]*"[^>]*>([^<]+)<'),
    ("job-title", r'class="[^"]*job-title[^"]*"[^>]*>([^<]+)<'),
    ("t-job-title", r'class="[^"]*t-job-title[^"]*"[^>]*>([^<]+)<'),
    ("has-job-title", r'has-job-title[^>]*>([^<]+)<'),
    ("b-job-title", r'b-job-title[^>]*>([^<]+)<'),
    ("card-title", r'data-title[^>]*>([^<]+)<'),
    ("data-job-title", r'data-job-title="([^"]+)"'),
]:
    titles = re.findall(pattern, html)
    if titles:
        print(f"\nPattern '{pattern_name}': found {len(titles)}")
        for t in titles[:5]:
            clean = t.strip()
            if clean and len(clean) > 3:
                print(f"  - {clean}")

# General job indicators
print("\n--- Page structure analysis ---")
for keyword in ["job", "vacancy", "position", "career", "apply", "location", "company"]:
    count = len(re.findall(r'\b' + keyword + r'\b', html[:50000], re.IGNORECASE))
    print(f"  '{keyword}' mentions: {count}")

# Check for job cards by class
cards = re.findall(r'<div[^>]*class="[^"]*(?:job-card|job-card-container|card-job|job-listing)[^"]*"[^>]*>', html)
print(f"\nJob card divs found: {len(cards)}")

# Check script tags for JSON
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
json_count = sum(1 for s in scripts if s.strip().startswith('{') or s.strip().startswith('window'))
print(f"Script tags: {len(scripts)}, JSON-like: {json_count}")

# Show a 2000-char section around where jobs might be
idx = html.find('job-search')
if idx == -1:
    idx = html.find('jobList')
if idx == -1:
    idx = html.find('vacancy')
if idx > 0:
    print(f"\n--- Content around job-search/Greek: ---")
    print(html[max(0,idx-100):idx+500][:1000])

print(f"\nTotal page size: {len(html):,} bytes")

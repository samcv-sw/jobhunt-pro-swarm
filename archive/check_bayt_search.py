import json
import re

import cloudscraper

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True, 'mobile': False})

# Try the Bayt search for network engineer
urls = [
    ("Bayt - network jobs", "https://www.bayt.com/en/international/jobs/network-jobs/"),
    ("Bayt - IT jobs", "https://www.bayt.com/en/international/jobs/it-jobs/"),
    ("Bayt - engineering jobs", "https://www.bayt.com/en/international/jobs/engineering-jobs/"),
    ("Bayt - Lebanon jobs", "https://www.bayt.com/en/lebanon/jobs/"),
    ("Bayt - UAE network jobs", "https://www.bayt.com/en/uae/jobs/network-jobs/"),
    ("Bayt - Saudi network jobs", "https://www.bayt.com/en/saudi-arabia/jobs/network-jobs/"),
]

for label, url in urls:
    try:
        resp = scraper.get(url, timeout=30)
        html = resp.text
        
        # Extract JSON-LD
        ld_json = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        
        job_items = []
        for j in ld_json:
            try:
                data = json.loads(j)
                items = data.get("itemListElement", [])
                for item in items:
                    if isinstance(item, dict):
                        url = item.get("url", "")
                        position = item.get("position", "")
                        job_items.append({"position": position, "url": url})
            except:
                pass
        
        print(f"\n=== {label} ===")
        print(f"  Status: {resp.status_code}")
        print(f"  Size: {len(html):,} bytes")
        print(f"  JSON-LD job items: {len(job_items)}")
        for ji in job_items[:10]:
            print(f"    [{ji['position']}] {ji['url']}")
            
    except Exception as e:
        print(f"\n=== {label} === ERROR: {e}")

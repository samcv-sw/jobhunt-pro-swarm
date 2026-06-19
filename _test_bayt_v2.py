"""Quick test Bayt.com from local PC"""
import cloudscraper, re

scraper = cloudscraper.create_scraper()
resp = scraper.get("https://www.bayt.com/en/international/jobs/network-jobs/", timeout=15)
print(f"HTTP {resp.status_code}, {len(resp.text)} bytes")

# Find job cards
titles = re.findall(r'<h2[^>]*class="[^"]*job-title[^"]*"[^>]*>(.*?)</h2>', resp.text, re.DOTALL)
companies = re.findall(r'<b[^>]*class="[^"]*company-name[^"]*"[^>]*>(.*?)</b>', resp.text, re.DOTALL)
print(f"Titles: {len(titles)}, Companies: {len(companies)}")
for t in titles[:5]:
    print(f"  {t.strip()}")

# Try JSON-LD
import json
ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', resp.text, re.DOTALL)
print(f"\nJSON-LD blocks: {len(ld)}")
for block in ld[:3]:
    try:
        data = json.loads(block)
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            items = data.get("itemListElement", [])
            print(f"  Items: {len(items)}")
            for item in items[:3]:
                print(f"    {json.dumps(item, indent=2)[:200]}")
    except:
        pass

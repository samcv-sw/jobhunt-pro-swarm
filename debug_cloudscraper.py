"""
Test cloudscraper bypass on Bayt
"""
import cloudscraper, json, re, urllib.parse

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False,
        'desktop': True,
    }
)

# Test Bayt search for network engineer in UAE
url = "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/"
resp = scraper.get(url, timeout=30)
html = resp.text
print(f"Status: {resp.status_code}, Length: {len(html)} chars", flush=True)

blocked = "cf-browser-verification" in html or "just a moment" in html.lower() or "turnstile" in html or "challenge-platform" in html
print(f"BLOCKED: {blocked}", flush=True)

title_match = re.search(r'<title>(.*?)</title>', html)
print(f"Title: {title_match.group(1) if title_match else 'N/A'}", flush=True)

# Search for job cards
h2s = re.findall(r'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/[^"]+)"[^>]*>(.*?)</a>.*?</h2>', html, re.DOTALL)
if h2s:
    print(f"\nFound {len(h2s)} job h2 links (first 3):", flush=True)
    for href, title_html in h2s[:3]:
        title_t = re.sub(r'<[^>]+>', '', title_html).strip()
        print(f"  - {title_t} -> {href[:60]}", flush=True)
else:
    # Try other patterns
    job_cards = re.findall(r'class="[^"]*job-title[^"]*"[^>]*>(.*?)<', html, re.DOTALL)
    print(f"\nNo h2 job links. 'job-title' class occurrences: {len(job_cards)}", flush=True)
    
    # Save for inspection
    with open("debug_cloudscraper.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved debug_cloudscraper.html", flush=True)

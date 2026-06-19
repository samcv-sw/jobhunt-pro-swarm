"""Bayt.com — extract ALL data from search results"""
import cloudscraper, json, re
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()
resp = scraper.get("https://www.bayt.com/en/international/jobs/network-jobs/", timeout=15)
print(f"HTTP {resp.status_code}, {len(resp.text)} bytes")

soup = BeautifulSoup(resp.text, "html.parser")

# Method 1: JSON-LD
ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', resp.text, re.DOTALL)
if ld:
    data = json.loads(ld[0])
    items = data.get("itemListElement", [])
    print(f"\n=== JSON-LD: {len(items)} items ===")

# Method 2: Look for job cards in HTML
cards = soup.select("li[class*=job], div[class*=job], article[class*=job], div[class*=card]")
print(f"\n=== HTML cards found: {len(cards)} ===")

# Method 3: Search for company names
companies = soup.find_all("b", class_=re.compile("company"))
print(f"Company <b> tags: {len(companies)}")
for c in companies[:5]:
    print(f"  {c.get_text(strip=True)[:50]}")

# Method 4: All <a> tags with jobs in href
job_links = soup.select("a[href*=jobs]")
print(f"\nJob links: {len(job_links)}")

# Method 5: Try data attributes
for tag in soup.find_all(["div", "li"], attrs={"data-*": True}):
    pass

# Method 6: Search for strings containing "company"
html_lower = resp.text.lower()
import_count = html_lower.count("company")
title_count = html_lower.count("job-title")
location_count = html_lower.count("location")
print(f"\nWord counts: company={import_count}, job-title={title_count}, location={location_count}")

# Method 7: Just dump first 3000 chars of HTML to see structure
print("\n=== HTML structure (first 2000 chars) ===")
print(resp.text[:2000])

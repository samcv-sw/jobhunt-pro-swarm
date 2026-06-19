"""Bayt.com — test RSS and individual job pages"""
import cloudscraper, json, re
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()

# Try RSS feed
tests = [
    "https://www.bayt.com/en/rss/jobs/network-jobs/",
    "https://www.bayt.com/en/international/jobs/network-jobs/",
    "https://www.bayt.com/en/api/job-search/?keyword=network&country=all",
    "https://www.bayt.com/en/saudi-arabia/jobs/network-engineer-5457405/",
    "https://www.bayt.com/en/qatar/jobs/network-specialist-5463265/",
    "https://www.bayt.com/en/qatar/jobs/it-network-engineer-5457087/",
]

for url in tests:
    try:
        resp = scraper.get(url, timeout=15)
        print(f"\n=== {url[:60]} ===")
        print(f"HTTP {resp.status_code}, {len(resp.text)} bytes")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # For RSS
        if "rss" in url:
            items = soup.select("item")
            print(f"RSS items: {len(items)}")
            for item in items[:2]:
                t = item.find("title")
                print(f"  {t.get_text(strip=True)[:80] if t else 'no title'}")
        
        # For individual job pages
        if "/jobs/" in url:
            # Company name
            comp = soup.select_one("a[class*=company]")
            if not comp:
                comp = soup.select_one("[class*=employer]")
            if not comp:
                comp = soup.find("a", href=re.compile(r"/en/company/"))
            print(f"Company: {comp.get_text(strip=True) if comp else 'not found'}")
            
            # Title
            h1 = soup.find("h1")
            print(f"Title: {h1.get_text(strip=True)[:60] if h1 else 'not found'}")
            
            # Location
            loc = soup.select_one("[class*=location]")
            print(f"Location: {loc.get_text(strip=True)[:40] if loc else 'not found'}")
            
            # JSON-LD
            ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', resp.text, re.DOTALL)
            if ld:
                for block in ld[:2]:
                    try:
                        data = json.loads(block)
                        print(f"LD type: {data.get('@type','?')}")
                        if data.get("@type") == "JobPosting":
                            print(f"  title: {data.get('title','')[:50]}")
                            print(f"  company: {data.get('hiringOrganization',{}).get('name','')}")
                            print(f"  location: {data.get('jobLocation',{})}")
                    except:
                        pass
    except Exception as e:
        print(f"\n=== {url[:50]} ===")
        print(f"ERROR: {e}")

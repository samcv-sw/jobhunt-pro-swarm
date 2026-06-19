import httpx, re, json, time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Google Jobs SERP — embedded structured data
urls = [
    ("Dubai", "https://www.google.com/search?q=network+engineer+jobs+in+Dubai&ibp=htl;jobs&hl=en&num=20"),
    ("Lebanon", "https://www.google.com/search?q=network+engineer+jobs+in+Beirut&ibp=htl;jobs&hl=en&num=20"),
    ("Saudi", "https://www.google.com/search?q=network+engineer+jobs+in+Riyadh&ibp=htl;jobs&hl=en&num=20"),
]

for name, url in urls:
    try:
        r = httpx.get(url, headers={"User-Agent": ua}, follow_redirects=True, timeout=15)
        print(f"\n=== Google Jobs: {name} ===")
        print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
        
        if r.status_code != 200:
            print(f"  FAILED")
            continue
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Method 1: Find LD+JSON structured data
        ld_json = soup.find_all("script", type="application/ld+json")
        print(f"  LD+JSON blocks: {len(ld_json)}")
        
        jobs_found = 0
        for script in ld_json:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") == "ItemList":
                        items = data.get("itemListElement", [])
                        for item in items:
                            job = item.get("item", {})
                            title = job.get("title", "")
                            company = ""
                            employer = job.get("hiringOrganization", {})
                            if isinstance(employer, dict):
                                company = employer.get("name", "")
                            location = job.get("jobLocation", [{}])
                            if isinstance(location, list) and location:
                                loc = location[0]
                            elif isinstance(location, dict):
                                loc = location
                            else:
                                loc = {}
                            city = ""
                            addr = loc.get("address", {})
                            if isinstance(addr, dict):
                                city = addr.get("addressLocality", "")
                            elif isinstance(addr, str):
                                city = addr
                            url2 = job.get("url", "")
                            if title and company:
                                jobs_found += 1
                                if jobs_found <= 3:
                                    print(f"    -> {title[:40]:40s} @ {company[:30]:30s} | {city}")
            except:
                pass
        
        if jobs_found == 0:
            # Method 2: Parse HTML for job cards
            cards = soup.select("div[class*=job]") or soup.select("div[data-*]") or []
            print(f"  HTML cards: {len(cards)}")
            for card in cards[:3]:
                print(f"    HTML: {card.get_text(strip=True)[:80]}")
                
    except Exception as e:
        print(f"\n  {name}: ERROR {e}")
    
    time.sleep(3)  # polite delay

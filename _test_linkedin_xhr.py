import httpx, re, time
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

with httpx.Client(headers={"User-Agent": ua}, follow_redirects=True, timeout=20) as c:
    
    # Test: XHR API with count=50
    print("=== LINKEDIN XHR API (count=50) ===")
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
           "?keywords=network+engineer&location=Dubai&start=0&count=50")
    r = c.get(url)
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes, {len(r.text)//1000}KB")
    
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("li") or soup.select(".job-search-card")
    print(f"  Jobs: {len(cards)}")
    
    for card in cards[:5]:
        title = card.select_one(".base-search-card__title") or card.select_one("h3")
        company = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
        location = card.select_one(".job-search-card__location")
        link = card.select_one("a[href*=jobs]")
        
        t = title.get_text(strip=True)[:40] if title else "?"
        c_name = company.get_text(strip=True)[:30] if company else "?"
        loc = location.get_text(strip=True)[:20] if location else "?"
        href = link.get("href", "")[:60] if link else "?"
        
        print(f"    {t:40s} @ {c_name:30s} | {loc}")
    
    # Test: multiple quick searches
    print("\n=== 10 SEARCHES (1 city × 10 titles) ===")
    titles = ["network engineer", "network administrator", "network technician",
              "it support engineer", "systems administrator", "network architect",
              "network security", "infrastructure engineer", "telecom engineer",
              "cctv engineer"]
    cities = ["Dubai"]
    
    total = 0
    start_time = time.time()
    for title in titles:
        for city in cities:
            url = (f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                   f"?keywords={quote_plus(title)}&location={quote_plus(city)}&start=0&count=50")
            r = c.get(url, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                cards = soup.select("li")
                total += len(cards)
                print(f"  {title[:30]:30s} | {city:15s} | {len(cards):3d} jobs")
            else:
                print(f"  {title[:30]:30s} | {city:15s} | FAIL {r.status_code}")
            time.sleep(0.3)  # minimal delay
    
    elapsed = time.time() - start_time
    print(f"\n  Total: {total} jobs from {len(titles)} queries in {elapsed:.1f}s")
    print(f"  Rate: {total/elapsed:.1f} jobs/second")

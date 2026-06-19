import httpx, json, re, time
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

with httpx.Client(headers={"User-Agent": ua}, follow_redirects=True, timeout=20) as c:
    
    # 1. LinkedIn JSON API (the XHR endpoint the page itself uses)
    print("=== LINKEDIN XHR API ===")
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
           "?keywords=network+engineer&location=Dubai&start=0&count=50")
    r = c.get(url)
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    print(f"  Starts: {r.text[:200]}")
    if r.status_code == 200 and r.text.strip().startswith("<"):
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("li") or soup.select(".job-search-card") or []
        print(f"  Job cards: {len(cards)}")
        for card in cards[:3]:
            title = card.select_one(".base-search-card__title") or card.select_one("h3")
            company = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
            link = card.select_one("a[href*=jobs]")
            t = title.get_text(strip=True)[:40] if title else "?"
            c_name = company.get_text(strip=True)[:30] if company else "?"
            print(f"    {t:40s} @ {c_name}")
    
    # 2. LinkedIn search with different experience levels
    print("\n=== LINKEDIN EXPERIENCE LEVELS ===")
    for exp in ["1,2", "2,3", "3,4", "1,2,3,4"]:
        url = f"https://www.linkedin.com/jobs/search/?keywords=network+engineer&location=Dubai&f_E={exp}"
        r = c.get(url, timeout=20)
        if r.status_code == 200:
            # Try to extract job count
            match = re.search(r'(\d+)\s*result', r.text)
            count = match.group(1) if match else "?"
            print(f"  f_E={exp:8s} -> HTTP 200, {len(r.text)//1000}KB, results: {count}")
        else:
            print(f"  f_E={exp:8s} -> HTTP {r.status_code}")
        time.sleep(1)
    
    # 3. LinkedIn with different sort
    print("\n=== LINKEDIN SORT VARIANTS ===")
    for sort in ["DD", "R"]:
        url = f"https://www.linkedin.com/jobs/search/?keywords=network+engineer&location=Dubai&sort={sort}"
        r = c.get(url, timeout=20)
        count = re.search(r'(\d+)\s*result', r.text) if r.status_code == 200 else None
        c_str = count.group(1) if count else "?"
        print(f"  sort={sort:2s} -> HTTP {r.status_code}, results: {c_str}")
        time.sleep(1)
    
    # 4. LinkedIn different job types
    print("\n=== LINKEDIN JOB TYPES ===")
    for jt in ["F", "C", "P", "F,C"]:
        url = f"https://www.linkedin.com/jobs/search/?keywords=network+engineer&location=Dubai&f_JT={jt}"
        r = c.get(url, timeout=20)
        count = re.search(r'(\d+)\s*result', r.text) if r.status_code == 200 else None
        c_str = count.group(1) if count else "?"
        print(f"  f_JT={jt:5s} -> HTTP {r.status_code}, results: {c_str}")
        time.sleep(1)

import httpx, re, time
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

with httpx.Client(headers={"User-Agent": ua}, follow_redirects=True, timeout=15) as c:
    
    # 1. DuckDuckGo HTML search
    print("=== DUCKDUCKGO ===")
    q = "network engineer Dubai job"
    r = c.get(f"https://html.duckduckgo.com/html/?q={quote_plus(q)}")
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            links.append((a.text.strip()[:50], href[:80]))
        print(f"  Results: {len(links)}")
        for t, h in links[:5]:
            print(f"    {t:50s} -> {h}")
    time.sleep(2)
    
    # 2. Indeed search page (not RSS)
    print("\n=== INDEED SEARCH PAGE ===")
    for loc in ["Dubai", ""]:
        url = f"https://www.indeed.com/jobs?q=network+engineer{'&l='+loc if loc else ''}&sort=date"
        r = c.get(url)
        print(f"  {loc or '(all)'}: HTTP {r.status_code}, {len(r.text)} bytes")
        if r.status_code == 200 and "jobs" in r.text.lower()[:2000]:
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("[data-jk]") or soup.select(".job_seen_beacon") or soup.select("a[href*=viewjob]")
            print(f"  Job cards: {len(cards)}")
            for card in cards[:2]:
                print(f"    {card.get_text(strip=True)[:80]}")
        time.sleep(1)
    
    # 3. Bing Search
    print("\n=== BING ===")
    q = "site:indeed.com 'network engineer' Dubai"
    r = c.get(f"https://www.bing.com/search?q={quote_plus(q)}&count=10")
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    if r.status_code == 200 and "job" in r.text.lower()[:1000]:
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select("li.b_algo h2 a") or soup.select("a[href*=indeed]")
        print(f"  Job links: {len(links)}")
        for a in links[:3]:
            href = a.get("href", "")
            print(f"    {a.text.strip()[:50]:50s} -> {href[:80]}")
    
    # 4. Indeed with curl UA (mimic curl)
    print("\n=== INDEED CURL UA ===")
    r = c.get("https://www.indeed.com/rss?q=network+engineer&sort=date",
              headers={"User-Agent": "curl/8.4.0", "Accept": "*/*"})
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes, starts: {r.text[:50]}")
    time.sleep(1)
    
    # 5. Indeed with Accept: application/xml
    print("\n=== INDEED XML ACCEPT ===")
    r = c.get("https://www.indeed.com/rss?q=network+engineer&sort=date",
              headers={"User-Agent": "Mozilla/5.0 (compatible)", "Accept": "application/rss+xml, application/xml"})
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes, starts: {r.text[:50]}")
    time.sleep(1)
    
    # 6. Indeed via Googlebot
    print("\n=== INDEED GOOGLEBOT ===")
    r = c.get("https://www.indeed.com/rss?q=network+engineer&sort=date",
              headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes, starts: {r.text[:50]}")

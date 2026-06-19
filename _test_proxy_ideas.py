import httpx, json, time
from bs4 import BeautifulSoup

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

with httpx.Client(headers={"User-Agent": ua}, follow_redirects=True, timeout=15) as c:
    
    # 1. Indeed via proxy-like approach: use url text proxy
    print("=== INDEED VIA JINA TEXT READER ===")
    for url in [
        "https://r.jina.ai/http://www.indeed.com/jobs?q=network+engineer&l=Dubai&sort=date",
        "https://r.jina.ai/http://www.indeed.com/rss?q=network+engineer&sort=date",
    ]:
        try:
            r = c.get(url, timeout=15)
            print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
            if r.status_code == 200:
                # Check if it contains job data
                keywords = ["network", "engineer", "job", "company", "Dubai"]
                found = sum(1 for k in keywords if k.lower() in r.text.lower())
                print(f"  Keywords found: {found}/{len(keywords)}")
                print(f"  First 150: {r.text[:150]}")
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(1)
    
    # 2. Gulftalent.com  
    print("\n=== GULFTALENT ===")
    try:
        r = c.get("https://www.gulftalent.com/jobs/network-engineer-jobs-in-uae")
        print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            titles = soup.find_all("h2") or soup.find_all("h3")
            for t in titles[:5]:
                text = t.get_text(strip=True)
                if text and len(text) > 5:
                    print(f"    {text[:60]}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # 3. Indeed with REAL browser headers (sec-ch-ua etc)
    print("\n=== INDEED BROWSER HEADERS ===")
    browser_h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    r = c.get("https://www.indeed.com/jobs?q=network+engineer&l=Dubai", headers=browser_h)
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("[data-jk]") or soup.select("a[href*=viewjob]")
        print(f"  Job cards: {len(cards)}")
        for card in cards[:2]:
            print(f"    {card.get_text(strip=True)[:80]}")
    else:
        print(f"  Block page: {r.text[200:500]}")

import httpx, re, json, time
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
h = {"User-Agent": ua, "Accept-Language": "en-US,en;q=0.9"}

with httpx.Client(headers=h, follow_redirects=True, timeout=15) as c:
    
    for loc in ["Dubai", "Abu Dhabi", "Riyadh", "Beirut", "Doha", "Kuwait"]:
        q = f"site:indeed.com OR site:linkedin.com/jobs OR site:naukrigulf.com OR site:gulftalent.com '{loc}' 'network engineer'"
        url = f"https://www.bing.com/search?q={quote_plus(q)}&count=20"
        
        r = c.get(url)
        print(f"\n=== Bing: {loc} ===")
        print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
        
        if r.status_code != 200:
            break
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extract results (li.b_algo h2 a or similar)
        results = []
        for li in soup.select("li.b_algo"):
            h2 = li.find("h2")
            a = h2.find("a") if h2 else None
            if not a:
                continue
            href = a.get("href", "")
            title = a.get_text(strip=True)
            
            # Get snippet
            snip = li.select_one(".b_caption p") or li.select_one(".b_lineclamp2")
            snippet = snip.get_text(strip=True) if snip else ""
            
            results.append({
                "title": title[:60],
                "url": href[:100],
                "snippet": snippet[:120]
            })
        
        print(f"  Results: {len(results)}")
        for res in results[:4]:
            print(f"    [{res['url'][8:20].replace('/',''):12s}] {res['title'][:50]}")
        
        time.sleep(2)  # polite delay

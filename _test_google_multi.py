import httpx, re, json, time
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup

# Test: Google search for Indeed/Bayt/LinkedIn jobs
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
h = {"User-Agent": ua}

queries = [
    ("LinkedIn", 'site:linkedin.com/jobs "network engineer" Dubai'),
    ("Indeed", 'site:indeed.com "network engineer" Dubai - rss'),
    ("Bayt", 'site:bayt.com "network engineer" Dubai'),
    ("NaukriGulf", 'site:naukrigulf.com "network engineer" Dubai'),
]

with httpx.Client(headers=h, follow_redirects=True, timeout=15) as client:
    for name, q in queries:
        url = f"https://www.google.com/search?q={quote_plus(q)}&num=10&hl=en"
        r = client.get(url)
        print(f"\n=== {name}: {q[:40]}...")
        print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
        
        if r.status_code != 200:
            print(f"  FAILED")
            continue
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Try to find job-like results
        links = []
        for g in soup.select("div.g") or soup.select("[data-hveid]"):
            a = g.find("a", href=True)
            if not a:
                continue
            href = a.get("href", "")
            # Clean google redirect
            if href.startswith("/url?"):
                qs = parse_qs(urlparse(href).query)
                href = qs.get("q", [href])[0]
            
            title = a.text.strip() or ""
            # Try to find company in snippet
            snippet = g.get_text(strip=True)[:200]
            
            links.append((href, title, snippet[:100]))
        
        print(f"  Results: {len(links)}")
        for href, title, snippet in links[:5]:
            print(f"    -> {title[:50]:50s}")
            print(f"       {href[:80]:80s}")
            print(f"       {snippet[:60]}...")
    
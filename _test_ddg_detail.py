import httpx
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
h = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.5", "DNT": "1"}

with httpx.Client(headers=h, follow_redirects=True, timeout=15) as c:
    # First visit homepage (get cookies)
    r = c.get("https://duckduckgo.com/", timeout=10)
    print(f"Home: HTTP {r.status_code}, cookies: {len(c.cookies)}")
    
    # Now search
    r = c.get("https://html.duckduckgo.com/html/?q=network+engineer+jobs+in+Dubai")
    print(f"\nSearch: HTTP {r.status_code}, {len(r.text)} bytes")
    print(f"First 500 chars: {r.text[:500]}")
    print(f"\nRemaining: {r.text[500:1200]}")

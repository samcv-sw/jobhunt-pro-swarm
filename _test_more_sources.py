import httpx, json, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

with httpx.Client(headers={"User-Agent": ua}, follow_redirects=True, timeout=15) as c:
    
    # 1. LinkedIn API — Job Postings JSON endpoint
    print("=== LINKEDIN JOBS API ===")
    url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPostings?keywords=network+engineer&location=Dubai&count=25&start=0"
    r = c.get(url)
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes, starts: {r.text[:100]}")
    if r.status_code == 200 and r.text.strip().startswith("{"):
        data = json.loads(r.text)
        print(f"  Items: {len(data.get('elements', []))}")
    
    # 2. LinkedIn Jobs Search page — check for embedded JSON
    print("\n=== LINKEDIN EMBEDDED DATA ===")
    url = "https://www.linkedin.com/jobs/search/?keywords=network+engineer&location=Dubai"
    r = c.get(url)
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    if r.status_code == 200:
        # Find embedded JSON data in script tags
        for script in re.findall(r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', r.text, re.DOTALL):
            try:
                data = json.loads(script)
                entities = data.get("entities", {}).get("jobPostings", {})
                print(f"  Embedded jobs: {len(entities)}")
                for jid, jdata in list(entities.items())[:3]:
                    print(f"    {jdata.get('title', '?')[:40]} @ {jdata.get('companyName', '?')[:30]}")
            except:
                print("  Embedded: parse error")
    
    # 3. Try `simplyhired.com` — another aggregator
    print("\n=== SIMPLYHIRED ===")
    r = c.get("https://www.simplyhired.com/search?q=network+engineer&l=Dubai")
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    if r.status_code == 200 and "job" in r.text.lower()[:2000]:
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("[data-jobkey]") or soup.select("a[href*=job]")
        print(f"  Cards: {len(cards)}")
    
    # 4. Try `jooble.org` — free aggregator  
    print("\n=== JOOIBLE ===")
    r = c.get("https://jooble.org/Search/Result?Keywords=network+engineer&Location=Dubai")
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("article") or soup.select("[class*=job]")
        print(f"  Cards: {len(cards)}")
    
    # 5. Indeed with query string variations
    print("\n=== INDEED VIA PLAYER / JOBSEEKER ===")
    for u in [
        "https://www.indeed.com/viewjob?jk=abc",  # direct job view
        "https://www.indeed.com",  # homepage
    ]:
        r = c.get(u)
        print(f"  {u[:40]:40s} -> HTTP {r.status_code}")
    
    # 6. test indeed with `fetch` (X-Requested-With)
    print("\n=== INDEED XHR STYLE ===")
    r = c.get("https://www.indeed.com/jobs?q=network+engineer&l=Dubai&sort=date",
              headers={"User-Agent": ua, "X-Requested-With": "XMLHttpRequest", "Accept": "text/html, */*"})
    print(f"  HTTP {r.status_code}, {len(r.text)} bytes")

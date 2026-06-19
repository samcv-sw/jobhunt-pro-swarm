import httpx, re
from bs4 import BeautifulSoup

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
h = {"User-Agent": ua, "Accept-Language": "en-US,en;q=0.9"}

with httpx.Client(headers=h, follow_redirects=True, timeout=15) as c:
    r = c.get("https://www.bing.com/search?q=network+engineer+jobs+in+Dubai")
    print(f"HTTP {r.status_code}, {len(r.text)} bytes")
    
    # Show first 1000 chars to understand structure
    print(f"\n--- First 1000 ---\n{r.text[:1000]}")
    
    # Find ALL links
    soup = BeautifulSoup(r.text, "html.parser")
    all_links = soup.find_all("a", href=True)
    print(f"\nAll links: {len(all_links)}")
    
    # Show links with job-related text
    for a in all_links[:20]:
        text = a.get_text(strip=True)
        href = a.get("href", "")
        if any(k in text.lower() for k in ["network", "engineer", "job", "apply", "career"]):
            if len(text) > 5:
                print(f"  {text[:60]:60s} -> {href[:80]}")
    
    # Find all li elements to see structure
    all_lis = soup.find_all("li")
    print(f"\nAll li elements: {len(all_lis)}")
    for li in all_lis[:15]:
        cls = li.get("class", "")
        text = li.get_text(strip=True)[:50]
        if any(k in text.lower() for k in ["network", "engineer", "job", "dubai"]):
            print(f"  class={cls}, text={text}")
        elif len(text) > 10:
            print(f"  class={cls}, text={text}")

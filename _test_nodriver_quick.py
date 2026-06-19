"""Quick test: nodriver with 3 titles x 2 countries"""
import asyncio, re, json
import nodriver as uc

TITLES = ["network engineer", "it support engineer", "devops engineer"]
COUNTRIES = [("uae", "UAE"), ("sa", "Saudi Arabia")]

async def main():
    browser = await uc.start(headless=False)
    all_jobs = []
    
    for title in TITLES:
        for cc, cn in COUNTRIES:
            url = f"https://www.bayt.com/en/{cc}/jobs/{title.replace(' ', '-')}-jobs/"
            page = await browser.get(url)
            await page.sleep(3)
            html = await page.get_content()
            
            h2s = re.findall(r'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/(?!search|network-engineer|it-support|devops|engineering|root)[^"]+)"[^>]*>(.*?)</a>.*?</h2>', html, re.DOTALL)
            for href, t_html in h2s:
                title_text = re.sub(r'<[^>]+>', '', t_html).strip().replace('&amp;', '&')
                if len(title_text) > 5 and 'jobs in' not in title_text.lower():
                    all_jobs.append({
                        'title': title_text, 'company': 'Unknown',
                        'url': f"https://www.bayt.com{href}",
                        'source': 'bayt', 'location': cn
                    })
            print(f"  {title[:25]}/{cc}: {len(h2s)} found")
            await asyncio.sleep(2)
    
    browser.stop()
    
    # Deduplicate
    seen = set()
    unique = [j for j in all_jobs if j['url'] not in seen and not seen.add(j['url'])]
    print(f"\nTOTAL: {len(unique)} unique Bayt jobs")
    
    # Upload
    import requests as req
    r = req.post("https://jhfguf.pythonanywhere.com/api/nodriver-feed", json={'jobs': unique}, timeout=30)
    print(f"PA: {r.status_code} - {r.text}")

asyncio.run(main())

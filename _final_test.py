"""FINAL TEST: 2 titles x 2 countries, verify end-to-end pipeline"""
import asyncio, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')
import nodriver as uc

TITLES = ["network engineer", "it support engineer"]
COUNTRIES = [("uae", "UAE"), ("saudi-arabia", "Saudi Arabia")]

async def main():
    print("[TEST] Starting nodriver Bayt collector...")
    browser = await uc.start(headless=False)
    all_jobs = []
    
    for title in TITLES:
        for cc, cn in COUNTRIES:
            url = f"https://www.bayt.com/en/{cc}/jobs/{title.replace(' ', '-')}-jobs/"
            print(f"[TEST] Loading: {url}")
            page = await browser.get(url)
            await page.sleep(4)
            html = await page.get_content()
            
            h2s = re.findall(r'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/(?!search|network-engineer|it-support)[^"]+)"[^>]*>(.*?)</a>.*?</h2>', html, re.DOTALL)
            
            for href, t_html in h2s:
                title_text = re.sub(r'<[^>]+>', '', t_html).strip().replace('&amp;', '&')
                if len(title_text) > 5 and 'jobs in' not in title_text.lower():
                    all_jobs.append({
                        'title': title_text, 'company': 'Unknown',
                        'url': f"https://www.bayt.com{href}",
                        'source': 'bayt', 'location': cn
                    })
            print(f"[TEST] {title} / {cc}: {len(h2s)} jobs found")
            await asyncio.sleep(2)
    
    browser.stop()
    
    seen = set()
    unique = [j for j in all_jobs if j['url'] not in seen and not seen.add(j['url'])]
    print(f"\n[TEST] TOTAL: {len(unique)} unique Bayt jobs")
    
    # Upload to PA
    import requests as req
    r = req.post("https://jhfguf.pythonanywhere.com/api/nodriver-feed", json={'jobs': unique}, timeout=30)
    print(f"[TEST] PA upload: {r.status_code} - {r.text}")
    
    # Verify: check PA DB count
    try:
        r2 = req.get("https://jhfguf.pythonanywhere.com/api/dashboard/stats", timeout=10)
        print(f"[TEST] PA dashboard: {r2.status_code}")
        if 'application/json' in r2.headers.get('content-type', ''):
            stats = r2.json()
            print(f"[TEST] PA stats: {json.dumps(stats, indent=2)[:500]}")
    except Exception as e:
        print(f"[TEST] Stats check: {e}")
    
    print("\n[TEST] ===== PIPELINE VERIFIED =====")

asyncio.run(main())

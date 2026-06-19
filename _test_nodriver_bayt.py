"""Nodriver: extract actual job data from Bayt's JS-rendered HTML"""
import asyncio, re, json
import nodriver as uc

async def test():
    browser = await uc.start(headless=False)
    page = await browser.get("https://www.bayt.com/en/uae/jobs/network-engineer-jobs/")
    await page.sleep(5)  # Wait for JS to render
    html = await page.get_content()
    
    # Find job cards with title + company
    # Approach: look for <h2> tags containing links to job pages
    h2s = re.findall(r'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/[^"]+)"[^>]*>(.*?)</a>.*?</h2>', html, re.DOTALL)
    print(f"H2 with job links: {len(h2s)}")
    for href, title_html in h2s[:5]:
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        print(f"  {title[:80]} | {href}")
    
    # Alternative: find all job links with titles
    links = re.findall(r'<a[^>]*href="(/en/[^/]+/jobs/(?!search|network|it-|executive|engineering|root)[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    print(f"\nJob-specific links: {len(links)}")
    seen = set()
    for href, title_html in links[:15]:
        if href not in seen:
            seen.add(href)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            if len(title) > 5:
                print(f"  {title[:80]} | {href}")
    
    # Find company names
    companies = re.findall(r'<a[^>]*href="(/en/[^/]+/)"[^>]*>(.*?)</a>', html)
    print(f"\nCompany links: {len(companies)}")
    for href, name in companies[:5]:
        clean = re.sub(r'<[^>]+>', '', name).strip()
        if len(clean) > 2:
            print(f"  {clean[:50]} | {href}")
    
    browser.stop()

asyncio.run(test())

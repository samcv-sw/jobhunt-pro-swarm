"""Test Indeed with nodriver"""
import asyncio, re, json
import nodriver as uc

async def test():
    browser = await uc.start(headless=False)
    
    # Test Indeed
    page = await browser.get("https://www.indeed.com/jobs?q=network+engineer&sort=date")
    await page.sleep(5)
    html = await page.get_content()
    
    # Look for job cards
    patterns = [
        'job_seen_beacon', 'jobCard', 'jobTitle', 'job-title', 
        'jobsearch', 'jmty', 'resultContent', 'slider_container',
        'jobTitle-ColorProtected', 'css-5lfssm'
    ]
    for p in patterns:
        count = html.count(p)
        if count > 0:
            print(f"  '{p}': {count} occurrences")
    
    # Check if bot challenge
    if 'captcha' in html.lower() or 'verify' in html.lower() or 'are you a human' in html.lower():
        print("  WARNING: Bot challenge detected!")
    
    # Extract all h2 tags
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    titles = [re.sub(r'<[^>]+>', '', h).strip() for h in h2s if re.sub(r'<[^>]+>', '', h).strip()]
    print(f"\n  H2 tags: {len(h2s)}")
    for t in titles[:10]:
        print(f"    {t[:80]}")
    
    browser.stop()

asyncio.run(test())

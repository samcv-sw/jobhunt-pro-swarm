"""Quick nodriver test - just prove it works"""
print("Step 1: Importing nodriver...")
import nodriver as uc
print("Step 2: Starting browser...")
import asyncio

async def test():
    browser = await uc.start(headless=False)
    print(f"Step 3: Browser started! Browser object: {type(browser).__name__}")
    
    page = await browser.get("https://www.bayt.com/en/uae/jobs/network-engineer-jobs/")
    print(f"Step 4: Page loaded - {page}")
    await page.sleep(3)
    
    html = await page.get_content()
    print(f"Step 5: HTML length: {len(html)}")
    
    # Just count job URLs
    import re
    jobs = re.findall(r'/en/uae/jobs/[^"]+/', html)
    urls = list(set(jobs))
    print(f"Step 6: Found {len(urls)} unique job URLs")
    if urls:
        for u in urls[:5]:
            print(f"  {u}")
    
    await browser.stop()
    print("Step 7: Browser stopped. Test complete!")

asyncio.run(test())

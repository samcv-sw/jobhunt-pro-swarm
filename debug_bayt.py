"""
Debug — fetch one Bayt page and save HTML to inspect
"""
import asyncio, nodriver as uc

async def main():
    browser = await uc.start(headless=True)
    url = "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/"
    page = await browser.get(url)
    await page.sleep(5)
    html = await page.get_content()
    
    with open("debug_bayt.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved debug_bayt.html ({len(html)} chars)", flush=True)
    
    # Also check for any job-related patterns
    h2_count = html.count("<h2")
    h3_count = html.count("<h3")
    a_count = html.count("job-title")
    print(f"<h2>: {h2_count}, <h3>: {h3_count}, 'job-title': {a_count}", flush=True)
    
    # Check for cloudflare/blocking
    if "cf-browser-verification" in html or "just a moment" in html.lower():
        print("BLOCKED: Cloudflare or challenge page", flush=True)
    else:
        print("Page loaded OK (no Cloudflare detected)", flush=True)
    
    # Check title
    import re
    titles = re.findall(r'<title>(.*?)</title>', html)
    print(f"Page title: {titles}", flush=True)
    
    browser.stop()

asyncio.run(main())

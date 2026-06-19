"""
Debug Bayt with user Chrome profile
"""
import asyncio, nodriver as uc

USER_DATA = "C:\\Users\\samde\\AppData\\Local\\Google\\Chrome\\User Data"

async def main():
    browser = await uc.start(
        headless=True,
        no_sandbox=True,
        user_data_dir=USER_DATA,
        browser_executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    )
    url = "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/"
    page = await browser.get(url)
    await page.sleep(6)
    html = await page.get_content()
    
    import re
    title_match = re.search(r'<title>(.*?)</title>', html)
    print(f"Page title: {title_match.group(1) if title_match else 'N/A'}", flush=True)
    
    blocked = "cf-browser-verification" in html or "just a moment" in html.lower() or "turnstile" in html or "verification" in html[:1000].lower()
    print(f"BLOCKED: {blocked}", flush=True)
    
    if not blocked:
        with open("debug_bayt_success.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved debug_bayt_success.html ({len(html)} chars)", flush=True)
    
    browser.stop()

asyncio.run(main())

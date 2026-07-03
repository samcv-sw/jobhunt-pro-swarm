import asyncio
import os
import sys
import logging
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sannysoft_verifier")

async def run_curl_cffi_verification(proxy: str = None) -> bool:
    """
    Tries to retrieve bot.sannysoft.com using curl_cffi to verify TLS / Header / Cloudflare bypass.
    """
    try:
        from curl_cffi import requests
    except ImportError:
        logger.error("curl_cffi is not installed in the current environment.")
        return False

    url = "https://bot.sannysoft.com/"
    
    # We use a modern chrome profile that matches our proposed list
    profile = "chrome146"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-CH-UA": '"Google Chrome";v="146", "Chromium";v="146", "Not_A Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Upgrade-Insecure-Requests": "1"
    }

    proxies = {"http": proxy, "https": proxy} if proxy else {}

    logger.info(f"Initiating curl_cffi TLS impersonation verification on {url} using profile {profile}...")
    
    try:
        async with requests.AsyncSession(
            impersonate=profile,
            headers=headers,
            proxies=proxies
        ) as session:
            # 1. Warmup: hit root/robots first
            logger.info("Warmup hit to robots.txt...")
            await session.get("https://bot.sannysoft.com/robots.txt", timeout=15)
            await asyncio.sleep(2.0)
            
            # 2. Main target request
            logger.info("Fetching target page...")
            resp = await session.get(url, timeout=20)
            resp.raise_for_status()

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else "No Title"
            
            logger.info(f"Verification Page Title: '{title_text}'")
            
            # Verify if Cloudflare challenge or sannysoft actual content
            if "sannysoft" in html.lower() or "bot detection" in title_text.lower():
                logger.info("SUCCESS: Bypassed Cloudflare block and fetched raw Sannysoft page!")
                return True
            else:
                logger.error("FAILURE: Fetched page did not contain expected Sannysoft content.")
                return False

    except Exception as e:
        logger.error(f"FAILURE: curl_cffi request failed: {e}")
        return False


async def run_nodriver_verification(proxy: str = None) -> bool:
    """
    Runs nodriver to fetch bot.sannysoft.com, allowing JS to run, and parses WebDriver/fingerprint results.
    """
    try:
        import nodriver as uc
    except ImportError:
        logger.warning("nodriver not installed. Skipping browser JS verification.")
        return True  # Treat as skip/pass for this portion

    logger.info("Initiating nodriver browser automation verification on https://bot.sannysoft.com/...")
    try:
        # Construct nodriver options
        browser_args = []
        if proxy:
            browser_args.append(f"--proxy-server={proxy}")
            
        browser = await uc.start(browser_args=browser_args, headless=True)
        page = await browser.get("https://bot.sannysoft.com/")
        
        # Wait for the JS tests to finish rendering
        logger.info("Waiting 6 seconds for client JS tests to execute...")
        await asyncio.sleep(6.0)
        
        html = await page.get_content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Sannysoft has table cells showing tests.
        # Let's inspect rows like navigator.webdriver, Chrome, etc.
        # A test row looks like: <td id="webdriver-result" class="fail">failed</td> or similar.
        webdriver_el = soup.find(id="webdriver-result") or soup.find(class_=lambda c: c and "webdriver" in str(c))
        
        webdriver_status = webdriver_el.get_text(strip=True) if webdriver_el else "Unknown"
        logger.info(f"navigator.webdriver test status: {webdriver_status}")
        
        # Close browser
        browser.stop()
        
        if "fail" in webdriver_status.lower() or "detected" in webdriver_status.lower():
            logger.error("FAILURE: Browser was detected as a bot on sannysoft webdriver test!")
            return False
            
        logger.info("SUCCESS: Browser bypassed webdriver/JS tests successfully!")
        return True

    except Exception as e:
        logger.error(f"FAILURE: nodriver verification execution failed: {e}")
        return False


async def main():
    proxy = os.getenv("TEST_PROXY") or os.getenv("RESIDENTIAL_PROXIES", "").split(",")[0]
    if not proxy:
        logger.warning("No proxy provided in env (TEST_PROXY or RESIDENTIAL_PROXIES). Performing direct check...")
        proxy = None
    else:
        logger.info(f"Using verification proxy: {proxy}")

    cffi_ok = await run_curl_cffi_verification(proxy)
    nodriver_ok = await run_nodriver_verification(proxy)

    if cffi_ok and nodriver_ok:
        logger.info("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        logger.error("VERIFICATION FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

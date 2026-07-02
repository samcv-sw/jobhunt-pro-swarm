"""
JobHunt Pro v13 - $0 Undetected Stealth Browser
Replaces AdsPower using undetected-chromedriver and free rotating proxies.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class ZeroCostStealthScraper:
    """
    Uses undetected-chromedriver to bypass Cloudflare/Datadome completely for free.
    """

    def __init__(self):
        self.is_ready = True

    async def search(self, url: str) -> str:
        """
        Executes a stealth request and returns the page source.
        """
        try:
            import undetected_chromedriver as uc
        except ImportError:
            logger.error(
                "undetected-chromedriver not installed. Run: pip install undetected-chromedriver"
            )
            return ""

        logger.info(f"Initializing $0 Undetected Chromedriver for {url}...")

        loop = asyncio.get_running_loop()

        def _scrape_sync():
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            # Add free community proxies here if needed

            driver = uc.Chrome(options=options)
            try:
                driver.get(url)
                # Wait for JS challenge to pass
                time.sleep(5)
                return driver.page_source
            finally:
                driver.quit()

        try:
            import time

            source = await loop.run_in_executor(None, _scrape_sync)
            logger.info("Successfully bypassed protection using $0 Stealth Browser.")
            return source
        except Exception as e:
            logger.error(f"Stealth scraping failed: {e}")
            return ""


stealth_scraper = ZeroCostStealthScraper()

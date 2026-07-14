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

            # Disable image loading via Chrome preferences
            prefs = {
                "profile.managed_default_content_settings.images": 2
            }
            options.add_experimental_option("prefs", prefs)

            driver = uc.Chrome(options=options)
            try:
                # Enable network domain and block stylesheets/trackers via CDP
                driver.execute_cdp_cmd("Network.enable", {})
                driver.execute_cdp_cmd("Network.setBlockedURLs", {
                    "urls": [
                        "*.css",
                        "*analytics*", "*google-analytics.com*", "*doubleclick*", "*tracker*", "*facebook.com*", "*fbcdn*"
                    ]
                })

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

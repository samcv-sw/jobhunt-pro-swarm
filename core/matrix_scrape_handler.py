import os
import sys
import argparse
import logging
import requests
import httpx
from pathlib import Path
from typing import Optional

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [MATRIX-SCRAPER] - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import scraper classes from multi_source_scraper
try:
    from core.multi_source_scraper import (
        BaseScraper,
        IndeedScraper,
        BaytScraper,
        WuzzufScraper,
        LinkedInScraper,
        GlassdoorScraper,
        NaukriScraper,
        DiceScraper,
        SeekScraper,
        StepStoneScraper,
        WWRScraper,
        WellfoundScraper,
        ZipRecruiterScraper,
        XingScraper,
        NaukriIndiaScraper,
        JoobleScraper,
        UpworkScraper,
    )
except ImportError as e:
    logger.error(f"Failed to import core scrapers: {e}")
    sys.exit(1)

SCRAPER_MAP = {
    "indeed": IndeedScraper,
    "bayt": BaytScraper,
    "wuzzuf": WuzzufScraper,
    "linkedin": LinkedInScraper,
    "glassdoor": GlassdoorScraper,
    "naukrigulf": NaukriScraper,
    "dice": DiceScraper,
    "seek": SeekScraper,
    "stepstone": StepStoneScraper,
    "wwr": WWRScraper,
    "wellfound": WellfoundScraper,
    "ziprecruiter": ZipRecruiterScraper,
    "xing": XingScraper,
    "naukriindia": NaukriIndiaScraper,
    "jooble": JoobleScraper,
    "upwork": UpworkScraper,
}

# Default queries & locations
QUERIES = [
    "network engineer",
    "system administrator",
    "it support engineer",
    "devops engineer",
]
LOCATIONS = ["Dubai", "Riyadh", "Beirut", "Doha", "Kuwait City", "Manama", "Muscat"]


def monkey_patch_scraper(worker_url: str):
    """Monkey patch BaseScraper._get to route requests through Cloudflare Worker Google Cache scrape."""
    original_get = BaseScraper._get

    def mock_get(
        self, url: str, extra_headers=None, max_retries=2
    ) -> Optional[httpx.Response]:
        logger.info(f"Routing request through Cloudflare Worker Scrape: {url}")
        try:
            # We fetch via worker router's scrape endpoint
            scrape_api_url = f"{worker_url.rstrip('/')}/scrape"
            resp = requests.get(scrape_api_url, params={"url": url}, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    logger.warning(
                        f"Worker scrape returned error for {url}: {data['error']}. Falling back to direct request."
                    )
                else:
                    content = data.get("content", "")
                    if content:
                        content_lower = content.lower()
                        block_indicators = [
                            "cf-challenge",
                            "cf-cookie-error",
                            "cf-browser-verification",
                            "attention required! | cloudflare",
                            "cloudflare ray id",
                            "ray id:",
                            "captcha-bypass",
                            "hcaptcha",
                            "recaptcha",
                        ]
                        if any(ind in content_lower for ind in block_indicators):
                            logger.warning(
                                f"Worker request for {url} returned a Cloudflare block page. Falling back to direct request."
                            )
                        else:
                            logger.info(
                                f"Successfully scraped {len(content)} bytes for {url}"
                            )
                            # Return mock httpx.Response object
                            mock_resp = httpx.Response(
                                status_code=200,
                                content=content.encode("utf-8"),
                                request=httpx.Request("GET", url),
                            )
                            return mock_resp
            else:
                logger.warning(
                    f"Worker returned status {resp.status_code} for {url}. Falling back to direct request."
                )
        except Exception as e:
            logger.error(
                f"Error fetching from worker scraper: {e}. Falling back to direct request."
            )

        # Fall back to original direct request
        logger.info(f"Executing original direct request fallback for {url}")
        return original_get(
            self, url, extra_headers=extra_headers, max_retries=max_retries
        )

    BaseScraper._get = mock_get
    logger.info(
        "BaseScraper._get successfully monkey-patched to use Cloudflare Worker."
    )


def main():
    parser = argparse.ArgumentParser(description="Matrix Scraper Handler")
    parser.add_argument(
        "--platform", required=True, help="Job platform to scrape (e.g. indeed, bayt)"
    )
    parser.add_argument("--page", type=int, default=0, help="Page offset/index")
    args = parser.parse_args()

    platform = args.platform.lower().strip()
    page = args.page

    worker_url = os.environ.get(
        "WORKER_URL", "https://jobhunt-pro-router.samsalameh-cv.workers.dev"
    )
    try:
        import config

        default_site = config.SITE_URL
    except Exception:
        default_site = "https://jhfguf.pythonanywhere.com"
    site_url = os.environ.get("SITE_URL", os.environ.get("PA_URL", default_site))

    # Install monkey patch
    monkey_patch_scraper(worker_url)

    # Get scraper class
    scraper_cls = SCRAPER_MAP.get(platform)
    if not scraper_cls:
        logger.warning(
            f"Platform '{platform}' is not supported by core scrapers. Skipping."
        )
        return

    # Choose a query and location randomly or based on page offset to cover all combinations
    query = QUERIES[page % len(QUERIES)]
    location = LOCATIONS[(page // len(QUERIES)) % len(LOCATIONS)]

    logger.info(
        f"Running scraper for Platform: {platform}, Query: '{query}', Location: '{location}', Page: {page}"
    )

    try:
        scraper = scraper_cls()
        # Custom search invocation to pass page limit / offset if supported, or standard search
        jobs = scraper.search(query=query, location=location, limit=15)
        logger.info(f"Scraper returned {len(jobs)} jobs")

        if jobs:
            # Format jobs for nodriver-feed endpoint
            feed_jobs = []
            for j in jobs:
                feed_jobs.append(
                    {
                        "title": j.get("title", ""),
                        "company": j.get("company", "Unknown"),
                        "url": j.get("url", ""),
                        "source": platform,
                        "location": j.get("location", location),
                        "email": j.get("email", ""),
                    }
                )

            # Run EmailFinder inside matrix_scrape_handler.py to find HR contact emails in cloud mode
            try:
                import asyncio
                from core.email_finder import EmailFinder

                async def enrich():
                    finder = EmailFinder()
                    return await finder.enrich_jobs(feed_jobs, fast=True)

                logger.info(f"Enriching {len(feed_jobs)} jobs with emails...")
                feed_jobs = asyncio.run(enrich())
                logger.info("Enrichment completed.")
            except Exception as finder_err:
                logger.error(f"Failed to enrich jobs with emails: {finder_err}")

            # 1. Upload to Cloudflare Worker D1 (Primary Cloud Storage)
            cf_feed_url = f"{worker_url.rstrip('/')}/api/jobs/feed"
            logger.info(
                f"Uploading {len(feed_jobs)} jobs to Cloudflare Worker D1: {cf_feed_url}..."
            )
            try:
                resp_cf = requests.post(
                    cf_feed_url, json={"jobs": feed_jobs}, timeout=30
                )
                if resp_cf.status_code == 200:
                    logger.info(
                        f"Successfully uploaded to CF Worker D1: {resp_cf.json()}"
                    )
                else:
                    logger.warning(
                        f"CF Worker D1 upload returned status: {resp_cf.status_code}"
                    )
            except Exception as cf_err:
                logger.error(f"Failed to upload to Cloudflare Worker D1: {cf_err}")

            # 2. Upload to PythonAnywhere's feed (Legacy Backup)
            feed_url = f"{site_url.rstrip('/')}/api/nodriver-feed"
            logger.info(
                f"Uploading {len(feed_jobs)} jobs to PythonAnywhere: {feed_url}..."
            )
            try:
                resp = requests.post(feed_url, json={"jobs": feed_jobs}, timeout=30)
                if resp.status_code == 200:
                    logger.info(f"Successfully uploaded to PA: {resp.json()}")
                else:
                    logger.error(
                        f"Failed to upload to PA. Status: {resp.status_code}, Response: {resp.text}"
                    )
            except Exception as pa_err:
                logger.error(f"Failed to upload to PythonAnywhere: {pa_err}")
        else:
            logger.info("No jobs found to upload.")

    except Exception as e:
        logger.exception(f"Scraper execution failed: {e}")


if __name__ == "__main__":
    main()

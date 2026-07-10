"""
JobHunt Pro — Bayt.com Job Scraper (Cloudflare bypass via cloudscraper)

Bayt.com is the #1 job board in the Middle East. It uses Cloudflare protection,
so we use cloudscraper (which mimics a real browser TLS fingerprint) to bypass it.

HTML structure (verified live):
  <ul class="media-list in-card ...">
    <li class="has-pointer-d">
      <h2><a href="/en/{country}/jobs/{title}-{id}/">Job Title</a></h2>
      <div class="job-company-location-wrapper">
        Company Name       (first text node)
        City , Country     (remaining text nodes, joined)
      </div>
    </li>
    ...

Search: Multiple countries & titles, 1s rate-limit between requests.
Returns clean job dicts: {company, title, location, url, source: "bayt"}.
"""

import asyncio
import logging
import random
import time

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

BAYT_BASE = "https://www.bayt.com"

# Country slugs (Bayt.com format)
COUNTRY_SLUGS = {
    "international": "international",
    "uae": "uae",
    "saudi-arabia": "saudi-arabia",
    "qatar": "qatar",
    "kuwait": "kuwait",
    "bahrain": "bahrain",
    "oman": "oman",
    "lebanon": "lebanon",
    "jordan": "jordan",
    "egypt": "egypt",
}

# Title slugs (URL-safe)
DEFAULT_TITLES = [
    "network-engineer",
    "network-administrator",
    "network-technician",
    "it-support-engineer",
    "system-administrator",
    "network-security",
]

DEFAULT_COUNTRIES = ["international", "uae", "saudi-arabia", "qatar", "kuwait"]

RATE_LIMIT = 1.0  # seconds between requests
REQUEST_TIMEOUT = 20  # seconds per request (Bayt can be slow)

# ═══════════════════════════════════════════════════════════════════════════════
# Scraper
# ═══════════════════════════════════════════════════════════════════════════════


def _get_scraper():
    """Get or create a cloudscraper instance with browser emulation."""
    if cloudscraper is None:
        raise ImportError(
            "cloudscraper is not installed. Run: pip install cloudscraper"
        )
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False,
        },
        delay=3,
    )
    return scraper


def _build_url(country: str, title: str) -> str:
    """Build Bayt.com search URL.

    Format: https://www.bayt.com/en/{country}/jobs/{title}-jobs/
    """
    country_slug = COUNTRY_SLUGS.get(country.lower(), country.lower())
    title_slug = title.lower().strip().replace(" ", "-")
    return f"{BAYT_BASE}/en/{country_slug}/jobs/{title_slug}-jobs/"


def _parse_job_cards(html: str) -> list[dict]:
    """Parse Bayt.com job listing HTML into job dicts.

    Verified structure (Jun 2026):
      <li class="has-pointer-d">
        <h2><a href="/en/{country}/jobs/{title}-{id}/">Job Title</a></h2>
        <div class="job-company-location-wrapper">
          CompanyName
          City , Country
        </div>
      </li>
    """
    jobs = []
    soup = BeautifulSoup(html, "html.parser")

    # Select job card <li> elements
    cards = soup.select("li.has-pointer-d")

    # Fallback: look for any card-like containers
    if not cards:
        cards = soup.select("[class*='job-card'], li[class*='job']")
    if not cards:
        # Last resort: find h2 with job links and use their parents
        cards = [
            h2.find_parent("li") or h2.parent
            for h2 in soup.select("h2 a[href*='/jobs/']")
        ]

    seen_urls = set()

    for card in cards:
        try:
            # ── Title & URL ──
            link = card.select_one("h2 a, a[href*='/jobs/']")
            if not link:
                link = card.select_one("a")
            if not link:
                continue

            job_title = link.get_text(strip=True)
            href = link.get("href", "")
            if not href or not job_title:
                continue

            # Normalize URL
            if href.startswith("/"):
                job_url = BAYT_BASE + href
            elif href.startswith("http"):
                job_url = href
            else:
                continue

            # Deduplicate
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            # ── Company & Location from wrapper ──
            wrapper = card.select_one(
                "div.job-company-location-wrapper, [class*='company'], "
                "[class*='location']"
            )

            company = "Unknown"
            location = ""

            if wrapper:
                # Get all text pieces from the wrapper as a list of stripped strings
                parts = [t.strip() for t in wrapper.stripped_strings]
                if parts:
                    company = parts[0]
                    # Remaining parts form the location (e.g., "Doha", ",", "Qatar")
                    loc_parts = [p for p in parts[1:] if p not in (",", "", " ")]
                    location = ", ".join(loc_parts)
            else:
                # Fallback: try standalone company/location selectors
                company_el = card.select_one(
                    "[class*='company'], [class*='employer'], b"
                )
                if company_el:
                    company = company_el.get_text(strip=True)
                loc_el = card.select_one("[class*='location'], [class*='city']")
                if loc_el:
                    location = loc_el.get_text(strip=True)

            # Clean up
            if not company or company in ("—", "-", ""):
                company = "Unknown"

            jobs.append(
                {
                    "company": company,
                    "title": job_title,
                    "location": location,
                    "url": job_url,
                    "source": "bayt",
                }
            )

        except Exception as e:
            logger.debug(f"Error parsing Bayt job card: {e}")
            continue

    return jobs


def _scrape_country_title(country: str, title: str) -> list[dict]:
    """Scrape a single country x title combination."""
    url = _build_url(country, title)

    try:
        scraper = _get_scraper()
        resp = scraper.get(url, timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            logger.warning(f"Bayt [{country}/{title}] HTTP {resp.status_code}")
            return []

        jobs = _parse_job_cards(resp.text)
        logger.info(f"Bayt [{country}/{title}]: {len(jobs)} jobs")
        return jobs

    except Exception as e:
        logger.error(f"Bayt [{country}/{title}] error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def search_bayt_sync(
    countries: list[str] | None = None,
    titles: list[str] | None = None,
    rate_limit: float = RATE_LIMIT,
    shuffle: bool = True,
) -> list[dict]:
    """Synchronously search Bayt.com across multiple countries and job titles.

    Args:
        countries: List of country slugs.
            Default: international, uae, saudi-arabia, qatar, kuwait
        titles: List of job title slugs.
            Default: network-engineer, network-administrator, etc.
        rate_limit: Seconds between requests. Default: 1.0
        shuffle: Shuffle search combos to distribute load. Default: True

    Returns:
        List of job dicts with keys: company, title, location, url, source
    """
    if countries is None:
        countries = DEFAULT_COUNTRIES
    if titles is None:
        titles = DEFAULT_TITLES

    # Build all search combos
    combos = [(c, t) for c in countries for t in titles]

    if shuffle:
        random.shuffle(combos)

    all_jobs = []
    seen_urls = set()

    for country, title in combos:
        jobs = _scrape_country_title(country, title)

        for job in jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)

        if rate_limit > 0 and jobs:
            time.sleep(rate_limit)

    return all_jobs


async def search_bayt(
    countries: list[str] | None = None,
    titles: list[str] | None = None,
    rate_limit: float = RATE_LIMIT,
) -> list[dict]:
    """Async wrapper for search_bayt_sync."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, search_bayt_sync, countries, titles, rate_limit
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    logger.debug("=" * 60)
    logger.debug("Bayt.com Scraper Test")
    logger.debug("=" * 60)

    jobs = search_bayt_sync(countries=["international"], titles=["network-engineer"])

    logger.debug(f"\nFound {len(jobs)} jobs")
    logger.debug("-" * 60)
    for j in jobs[:10]:
        logger.debug(f"  {j['company']}: {j['title']}")
        logger.debug(f"    {j['location']} | {j['url']}")
        logger.debug()
    if len(jobs) > 10:
        logger.debug(f"  ... and {len(jobs) - 10} more")
    logger.debug("=" * 60)

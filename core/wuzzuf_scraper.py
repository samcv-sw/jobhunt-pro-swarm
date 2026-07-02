"""
JobHunt Pro — Wuzzuf Job Scraper

Wuzzuf is a leading MENA (Middle East & North Africa) job board, based in Egypt.
Covers Egypt, UAE, Saudi Arabia, Qatar, Kuwait, and other MENA markets.

Wuzzuf has a RESTful search endpoint:
  https://wuzzuf.net/search/jobs/?q={title}&l={location}&start=0

HTML structure (verified):
  <div class="css-1gatmva e1v1l3u10">
    <h2 class="css-m604qf"><a href="/en/jobs/p/...">Job Title</a></h2>
    <a class="css-17s97q8">Company Name</a>
    <span class="css-5wys0k">City, Country</span>
  </div>

Returns job dicts: {company, title, location, url, source: "wuzzuf"}
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus

try:
    from curl_cffi.requests import AsyncSession as httpx_AsyncClient
except ImportError:
    import httpx

    httpx_AsyncClient = httpx.AsyncClient
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

WUZZUF_BASE = "https://wuzzuf.net"

LOCATIONS = {
    "egypt": "Egypt",
    "uae": "United+Arab+Emirates",
    "saudi-arabia": "Saudi+Arabia",
    "qatar": "Qatar",
    "kuwait": "Kuwait",
    "bahrain": "Bahrain",
    "oman": "Oman",
    "lebanon": "Lebanon",
    "jordan": "Jordan",
}

DEFAULT_TITLES = [
    "network engineer",
    "network administrator",
    "network technician",
    "it support engineer",
    "system administrator",
    "network security",
]

DEFAULT_LOCATIONS = ["egypt", "uae", "saudi-arabia", "qatar", "kuwait"]

RATE_LIMIT = 1.0
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Scraper
# ═══════════════════════════════════════════════════════════════════════════════


def _build_url(title: str, location: str) -> str:
    """Build Wuzzuf search URL.

    Format: https://wuzzuf.net/search/jobs/?q={title}&l={location}
    """
    loc_encoded = LOCATIONS.get(location.lower().replace(" ", "-"), location)
    return f"{WUZZUF_BASE}/search/jobs/?q={quote_plus(title)}&l={loc_encoded}"


def _parse_job_cards(html: str) -> List[Dict]:
    """Parse Wuzzuf job listing HTML.

    Wuzzuf structure:
      <div class="css-1gatmva e1v1l3u10">         (job card container)
        <h2 class="css-m604qf">
          <a href="/en/jobs/p/UUID-...">Job Title</a>
        </h2>
        <a class="css-17s97q8">Company Name</a>
        <span class="css-5wys0k">City, Country</span>
      </div>
    """
    jobs = []
    soup = BeautifulSoup(html, "html.parser")

    # Primary selector: Wuzzuf job card containers
    # Structure: div.css-ghe2tq.e1v1l3u10
    cards = soup.select(
        "div.css-ghe2tq.e1v1l3u10, "
        "div.css-ghe2tq, "
        "[class*='e1v1l3u10'], "
        "div[class*='job-card'], "
        "div[class*='JobCard']"
    )

    # Fallback: look for typical Wuzzuf pattern
    if not cards:
        cards = soup.select("h2 a[href*='/jobs/p/']")
        cards = [
            c.find_parent("div", class_=lambda x: x and "css" in (x or "")) or c.parent
            for c in cards
        ]

    # Last fallback: any h2 with job links
    if not cards:
        cards = soup.select("h2:has(a[href*='/jobs/'])")

    seen_urls = set()

    for card in cards:
        try:
            # ── Title & URL ──
            # Wuzzuf: h2.css-193uk2c > a.css-o171kl
            link = card.select_one(
                "h2 a[href*='/jobs/p/'], "
                "h2 a[href*='/jobs/'], "
                "a[href*='/en/jobs/'], "
                "a[href*='/jobs/p/']"
            )
            if not link:
                link = card.select_one("a[href*='/jobs/']")
            if not link:
                continue

            job_title = link.get_text(strip=True)
            href = link.get("href", "")
            if not href or not job_title:
                continue

            # Normalize URL
            if href.startswith("/"):
                job_url = WUZZUF_BASE + href
            elif href.startswith("http"):
                job_url = href
            else:
                continue

            # Deduplicate
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            # ── Company ──
            # Wuzzuf: company is in <a> to /jobs/careers/...
            # Note: first match is often empty; we pick the one with text
            company = "Unknown"
            for a in card.select("a[href*='/jobs/careers/']"):
                txt = a.get_text(strip=True)
                if txt:
                    company = txt.rstrip(" -").strip()
                    break

            if not company or company in ("—", "-", ""):
                company = "Unknown"

            # ── Location ──
            # Wuzzuf: location in span.css-16x61xq (e.g. "Maadi,Cairo,Egypt")
            loc_el = card.select_one(
                "span.css-16x61xq, span[class*='16x61xq'], span[class*='eoyjyou0']"
            )
            location = ""
            if loc_el:
                location = loc_el.get_text(strip=True)

            # Clean company
            if not company or company in ("—", "-", ""):
                company = "Unknown"

            jobs.append(
                {
                    "company": company,
                    "title": job_title,
                    "location": location,
                    "url": job_url,
                    "source": "wuzzuf",
                }
            )

        except Exception as e:
            logger.debug(f"Error parsing Wuzzuf card: {e}")
            continue

    return jobs


def _scrape_location_title(title: str, location_key: str) -> List[Dict]:
    """Scrape a single title x location combination."""
    url = _build_url(title, location_key)

    try:
        import cloudscraper

        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        resp = scraper.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            logger.warning(f"Wuzzuf [{location_key}/{title}] HTTP {resp.status_code}")
            return []

        jobs = _parse_job_cards(resp.text)
        logger.info(f"Wuzzuf [{location_key}/{title}]: {len(jobs)} jobs found")
        return jobs

    except Exception as e:
        logger.error(f"Wuzzuf [{location_key}/{title}] error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def search_wuzzuf_sync(
    titles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    rate_limit: float = RATE_LIMIT,
    shuffle: bool = True,
) -> List[Dict]:
    """Synchronously search Wuzzuf across multiple titles and locations.

    Args:
        titles: Job title strings. Default: network engineer, network admin, etc.
        locations: Location keys (egypt, uae, saudi-arabia, qatar, kuwait).
        rate_limit: Seconds between requests. Default: 1.0
        shuffle: Shuffle search combos. Default: True

    Returns:
        List of job dicts: company, title, location, url, source
    """
    if titles is None:
        titles = DEFAULT_TITLES
    if locations is None:
        locations = DEFAULT_LOCATIONS

    combos = [(t, l) for t in titles for l in locations]
    if shuffle:
        import random

        random.shuffle(combos)

    all_jobs = []
    seen_urls = set()

    for title, loc in combos:
        jobs = _scrape_location_title(title, loc)
        for job in jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)
        if rate_limit > 0 and jobs:
            time.sleep(rate_limit)

    return all_jobs


async def search_wuzzuf(
    titles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    rate_limit: float = RATE_LIMIT,
) -> List[Dict]:
    """Async wrapper for search_wuzzuf_sync."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, search_wuzzuf_sync, titles, locations, rate_limit
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("=" * 60)
    print("Wuzzuf Scraper Test")
    print("=" * 60)

    jobs = search_wuzzuf_sync(
        titles=["network engineer"],
        locations=["saudi-arabia"],
    )

    print(f"\nFound {len(jobs)} jobs")
    print("-" * 60)
    for j in jobs[:10]:
        print(f"  {j['company']}: {j['title']}")
        print(f"    {j['location']} | {j['url']}")
        print()
    if len(jobs) > 10:
        print(f"  ... and {len(jobs) - 10} more")
    print("=" * 60)

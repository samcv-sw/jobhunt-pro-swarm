"""
JobHunt Pro — Dice.com Job Scraper

Dice.com is a major US tech job board. Lists remote/onsite jobs globally.
Server-rendered Tailwind CSS SPA (no JS rendering needed).

HTML structure (verified live, Jun 2026):
  <div class="@container/job-list">
    <div class="flex flex-col ...">  <!-- wrapper -->
      <div class="flex flex-col gap-6 overflow-hidden rounded-lg border ...">
        <span class="logo ...">Company Name</span>
        <a href="/job-detail/{uuid}/">Job Title</a>
        <span class="inline-flex h-5 w-full ...">Location •Date</span>
      </div>
      ...

Search: network-engineer + Dubai, Abu Dhabi, Riyadh, Doha, Kuwait
Returns job dicts: {company, title, location, url, source: "dice"}
"""

import asyncio
import logging
import time
import re
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

DICE_BASE = "https://www.dice.com"

LOCATIONS = {
    "dubai": "Dubai%2C+United+Arab+Emirates",
    "abu-dhabi": "Abu+Dhabi%2C+United+Arab+Emirates",
    "riyadh": "Riyadh%2C+Saudi+Arabia",
    "doha": "Doha%2C+Qatar",
    "kuwait": "Kuwait+City%2C+Kuwait",
}

DEFAULT_TITLES = [
    "network+engineer",
    "network+administrator",
    "network+technician",
    "IT+support+engineer",
    "system+administrator",
    "network+security",
    "Infrastructure+Engineer",
    "DevOps+Engineer",
]

DEFAULT_LOCATIONS = ["dubai", "abu-dhabi", "riyadh", "doha", "kuwait"]

RATE_LIMIT = 0.5
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.dice.com/",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Scraper
# ═══════════════════════════════════════════════════════════════════════════════

def _build_url(title: str, location: str) -> str:
    """Build Dice.com search URL."""
    loc_encoded = LOCATIONS.get(location.lower().replace(" ", "-"), location)
    return f"{DICE_BASE}/jobs?q={title}&location={loc_encoded}"


def _extract_location(text: str) -> str:
    """
    Dice location format: 'Remote•Today', 'Remote or City, State•Today',
    'City, State•3d ago'
    Extract just the location part (before the • bullet).
    """
    if not text:
        return ""
    # Split on bullet • and take the first part
    location = text.split("•")[0].strip()
    # Clean up "Remote or X" -> "X" if there's a specific location
    match = re.match(r"Remote\s+or\s+(.+)$", location)
    if match:
        return match.group(1).strip()
    return location


def _parse_job_cards(html: str) -> List[Dict]:
    """Parse Dice.com job listing HTML.

    Card structure:
      <div class="flex flex-col gap-6 overflow-hidden rounded-lg border bg-surface-primary p-6 ...">
        <span class="logo ...">Company Name</span>
        <a href="/job-detail/{uuid}/">Job Title</a>
        <span class="inline-flex h-5 w-full ...">Location •Date</span>
      </div>
    """
    jobs = []
    soup = BeautifulSoup(html, "html.parser")

    # Try multiple card selectors
    cards = soup.select(
        "div[class*='overflow-hidden'][class*='rounded-lg'][class*='border']"
        "[class*='bg-surface-primary']"
    )

    if not cards:
        cards = soup.select("div[class*='overflow-hidden rounded-lg border']")

    if not cards:
        # Fallback: find all links to /job-detail/ and group by parent
        seen_parents = set()
        for a in soup.select("a[href*='/job-detail/']"):
            card = a.find_parent(
                "div", class_=lambda c: c and "rounded" in " ".join(c)
            ) or a.parent
            if card and card not in seen_parents:
                seen_parents.add(card)
                cards = list(seen_parents)

    seen_urls = set()

    for card in cards:
        try:
            # ── Company ──
            company_el = card.select_one(
                "span[class*='logo'], span[class*='company'], "
                "[class*='logo']"
            )
            company = "Unknown"
            if company_el:
                company = company_el.get_text(strip=True)

            # ── Title & URL ──
            # The title link is typically the 2nd link, but let's be precise
            for a in card.select("a[href*='/job-detail/']"):
                href = a.get("href", "")
                title = a.get_text(strip=True)

                # Skip action links
                if not title or title in ("Easy Apply", "Apply Now", ""):
                    continue

                # Normalize URL
                if href.startswith("/"):
                    job_url = DICE_BASE + href
                elif href.startswith("http"):
                    job_url = href
                else:
                    continue

                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                # ── Location ──
                loc_el = card.select_one("span[class*='inline-flex h-5 w-full'],[class*='inline-flex'][class*='h-5'][class*='w-full'],span[class*='h-5 w-full']")
                location = ""
                if loc_el:
                    raw_loc = loc_el.get_text(strip=True)
                    location = _extract_location(raw_loc)

                jobs.append({
                    "company": company,
                    "title": title,
                    "location": location if location else "",
                    "url": job_url,
                    "source": "dice",
                })

        except Exception as e:
            logger.debug(f"Error parsing Dice card: {e}")
            continue

    return jobs


def _scrape_location_title(title: str, location_key: str) -> List[Dict]:
    """Scrape a single title x location combination."""
    url = _build_url(title, location_key)

    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        })
        resp = scraper.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            logger.warning(f"Dice [{location_key}/{title}] HTTP {resp.status_code}")
            return []

        jobs = _parse_job_cards(resp.text)
        logger.info(f"Dice [{location_key}/{title}]: {len(jobs)} jobs found")
        return jobs

    except Exception as e:
        logger.error(f"Dice [{location_key}/{title}] error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def search_dice_sync(
    titles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    rate_limit: float = RATE_LIMIT,
    shuffle: bool = True,
) -> List[Dict]:
    """Synchronously search Dice.com across multiple titles and locations.

    Args:
        titles: Job title query strings. Default: network+engineer, etc.
        locations: Location keys (dubai, abu-dhabi, riyadh, doha, kuwait).
        rate_limit: Seconds between requests. Default: 0.5
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


async def search_dice(
    titles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    rate_limit: float = RATE_LIMIT,
) -> List[Dict]:
    """Async wrapper for search_dice_sync."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, search_dice_sync, titles, locations, rate_limit
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("=" * 60)
    print("Dice.com Scraper Test")
    print("=" * 60)

    jobs = search_dice_sync(titles=["network+engineer"], locations=["dubai"])

    print(f"\nFound {len(jobs)} jobs")
    print("-" * 60)
    for j in jobs[:10]:
        print(f"  {j['company']}: {j['title']}")
        print(f"    {j['location']} | {j['url']}")
        print()
    if len(jobs) > 10:
        print(f"  ... and {len(jobs) - 10} more")
    print("=" * 60)

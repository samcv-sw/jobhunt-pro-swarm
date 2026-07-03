# Proposed Code Changes for `scrapers/stealth_ingest.py`

This patch improves stealth capability, rotating residential proxies (with fallback to core/stealth's free harvesting proxy pool), TLS fingerprint spoofing, cookie handling, and random delay logic.

```python
import asyncio
import random
import logging
import urllib.parse
from typing import List, Dict, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
import os

logger = logging.getLogger(__name__)

# Load residential proxies from environment variables
RESIDENTIAL_PROXIES = [p.strip() for p in os.getenv("RESIDENTIAL_PROXIES", "").split(",") if p.strip()]

# Advanced browser impersonation profiles supported by curl_cffi
STEALTH_PROFILES = [
    "chrome120", 
    "chrome131", 
    "chrome136", 
    "safari18_0", 
    "safari18_0_ios", 
    "firefox133"
]

def get_random_proxy() -> dict:
    """
    Retrieves a proxy config.
    Prioritizes user-supplied RESIDENTIAL_PROXIES.
    If not configured, falls back to the dynamic elite proxy scraper logic
    defined in core/stealth.py's global instance to prevent empty proxy failures.
    """
    if RESIDENTIAL_PROXIES:
        proxy = random.choice(RESIDENTIAL_PROXIES)
        return {"http": proxy, "https": proxy}
        
    try:
        from core.stealth import stealth
        harvested_proxy = stealth.get_random_proxy()
        if harvested_proxy:
            return {"http": harvested_proxy, "https": harvested_proxy}
    except Exception as e:
        logger.warning(f"Failed to harvest fallback proxy: {e}")
        
    return {}

def _parse_job_page(html: str, source_url: str) -> dict | None:
    """
    Parses a job page HTML and returns a structured dict with title and url.
    Returns None if parsing fails or if Cloudflare blocking screen is detected.
    """
    if not html:
        return None
        
    # Check for common bot blocking/Cloudflare strings
    is_blocked = any(term in html.lower() for term in ["just a moment", "attention required", "turnstile", "ray id", "ddg-captcha"])
    if is_blocked:
        logger.error(f"Anti-bot block screen detected on page: {source_url}")
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Extract job title — try common selectors in priority order
        title_el = (
            soup.find("h1")
            or soup.find(attrs={"class": lambda c: c and "job-title" in c})
            or soup.find(attrs={"class": lambda c: c and "title" in c})
            or soup.find("title")
        )
        title = title_el.get_text(strip=True) if title_el else "Unknown Position"

        # Extract company name if present
        company_el = soup.find(attrs={"class": lambda c: c and "company" in str(c).lower()})
        company = company_el.get_text(strip=True) if company_el else None

        # Extract description snippet (first 500 chars of body text)
        body_text = soup.get_text(separator=" ", strip=True)
        description_snippet = body_text[:500] if body_text else ""

        return {
            "title": title,
            "url": source_url,
            "company": company,
            "description_snippet": description_snippet,
        }
    except Exception as e:
        logger.error(f"Parsing error for {source_url}: {e}")
        return None

def _get_stealth_headers(impersonate_profile: str, root_domain: str) -> Dict[str, str]:
    """
    Generates realistic, matching HTTP/2 headers for the given impersonate profile.
    Avoids header mismatches that reveal bot status to server profiling engines.
    """
    parsed = urllib.parse.urlparse(root_domain)
    host = parsed.netloc

    # Base headers
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Host": host,
        "Connection": "keep-alive"
    }

    # Add profile-specific header adaptations
    if "chrome" in impersonate_profile:
        headers["sec-ch-ua"] = '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"'
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = '"Windows"'
    elif "safari" in impersonate_profile:
        headers.pop("Connection", None)  # Safari prefers HTTP/2 keep-alive defaults without explicit Connection header
    elif "firefox" in impersonate_profile:
        headers["Accept-Language"] = "en-US,en;q=0.5"

    return headers

async def process_single_job(url: str) -> dict | None:
    """
    Fetches a single job URL with advanced stealth session isolation, 
    custom HTTP/2 headers matching the spoofed profile, cookie preservation,
    organic warmup, and random jitter delays.
    """
    proxy_config = get_random_proxy()
    impersonate_profile = random.choice(STEALTH_PROFILES)
    
    parsed_uri = urllib.parse.urlparse(url)
    root_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
    headers = _get_stealth_headers(impersonate_profile, root_domain)

    # Initialize AsyncSession with native TLS fingerprint spoofing and proxy config
    async with requests.AsyncSession(
        impersonate=impersonate_profile,
        proxies=proxy_config,
        headers=headers,
    ) as session:
        try:
            # Add dynamic X-Forwarded-For if no proxy is configured (fallback mitigation)
            if not proxy_config:
                session.headers["x-forwarded-for"] = (
                    f"{random.randint(1,255)}.{random.randint(1,255)}"
                    f".{random.randint(1,255)}.{random.randint(1,255)}"
                )

            # 1. Organic Warmup Steps: Hit the home page first to collect cookies and build session state
            logger.info(f"Stealth warmup: accessing root domain {root_domain} with {impersonate_profile}")
            warmup_headers = headers.copy()
            warmup_headers["Sec-Fetch-Site"] = "none"
            
            warmup_res = await session.get(root_domain, headers=warmup_headers, timeout=15)
            warmup_res.raise_for_status()

            # Random jitter delay (simulate human reading time / typing delay)
            delay = random.uniform(3.0, 7.0)
            logger.info(f"Warmup successful. Delaying for {delay:.2f}s before fetching target job...")
            await asyncio.sleep(delay)

            # 2. Fetch the target job page with referer and dynamic session cookies intact
            headers["Sec-Fetch-Site"] = "same-origin"
            headers["Referer"] = root_domain
            
            logger.info(f"Stealth fetch: accessing target URL {url}")
            response = await session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            return _parse_job_page(response.text, url)

        except Exception as e:
            logger.error(f"Failed to stealth-fetch {url}: {e}")
            return None

async def stealth_scrape_jobs(urls: List[str]) -> List[dict]:
    """
    Main stealth scraping engine.
    Iterates sequentially or with limited concurrency to avoid parallel pattern detection.
    """
    results = []
    for url in urls:
        res = await process_single_job(url)
        if res:
            results.append(res)
        # Random sleep between distinct page scrapes
        await asyncio.sleep(random.uniform(2.0, 4.0))

    logger.info(f"Stealth scrape complete: {len(results)}/{len(urls)} pages parsed successfully.")
    return results
```

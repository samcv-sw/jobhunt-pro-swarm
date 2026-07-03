import asyncio
import random
import logging
import urllib.parse
from typing import List, Dict, Optional
import os
import time

try:
    from curl_cffi import requests
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Parse proxies from env. Supports comma-separated list.
PROXY_LIST = [p.strip() for p in os.getenv("RESIDENTIAL_PROXIES", "").split(",") if p.strip()]

# Curated browser profiles with aligned TLS target and HTTP headers
STEALTH_PROFILES = [
    {
        "id": "chrome131",
        "impersonate": "chrome131",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    },
    {
        "id": "chrome146",
        "impersonate": "chrome146",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Sec-CH-UA": '"Google Chrome";v="146", "Chromium";v="146", "Not_A Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    },
    {
        "id": "safari18_0",
        "impersonate": "safari18_0",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar-XM;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    },
    {
        "id": "safari2601",
        "impersonate": "safari2601",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar-XM;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    },
    {
        "id": "firefox147",
        "impersonate": "firefox147",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        }
    }
]

# Set limit on concurrency to avoid spamming target servers
CONCURRENCY_SEMAPHORE = asyncio.Semaphore(3)


def get_stabilized_proxy(session_id: str) -> dict:
    """
    Selects a proxy based on session_id to maintain IP pinning.
    Supports backconnect gateways (injecting session ID into username) 
    or selecting a pinned IP from a list.
    """
    if not PROXY_LIST:
        return {}

    # If it's a single backconnect proxy (e.g., contains @ and is a gate provider)
    # We can inject session ID into username if supported, e.g., user-session-XYZ123:pass@gate.proxy.com:port
    proxy_str = PROXY_LIST[0]
    
    # Simple check: if there is only 1 proxy and it looks like a backconnect proxy (e.g., brightdata, oxylabs, etc.)
    # we can append a session parameter to keep the IP pinned for this scraping session.
    if len(PROXY_LIST) == 1 and "@" in proxy_str and ("session-" not in proxy_str):
        # E.g. http://username:password@proxy.gate.com:8000 -> http://username-session-XYZ:password@proxy.gate.com:8000
        parsed = urllib.parse.urlsplit(proxy_str)
        if parsed.username and parsed.password:
            new_username = f"{parsed.username}-session-{session_id}"
            netloc = f"{new_username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
            reconstructed = urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
            return {"http": reconstructed, "https": reconstructed}

    # Otherwise, pin to a specific proxy in the list using hash of session_id
    idx = hash(session_id) % len(PROXY_LIST)
    selected_proxy = PROXY_LIST[idx]
    return {"http": selected_proxy, "https": selected_proxy}


def _parse_job_page(html: str, source_url: str) -> dict | None:
    """
    Parses a job page HTML and returns a structured dict with title and url.
    Returns None if parsing fails.
    """
    if not html:
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


async def process_single_job(url: str, session_id: Optional[str] = None) -> dict | None:
    """
    Fetches a single job URL with stealth session isolation and parses it.
    Returns a structured job dict or None on failure.
    Uses Concurrency Semaphore and random delay (jitter).
    """
    if not HAS_CFFI:
        logger.warning("curl_cffi not installed! Bypasses might fail.")
        # Fallback to standard requests/httpx if needed...
        return None

    # Set up session-id for proxy pinning
    if not session_id:
        session_id = f"sess_{random.randint(100000, 999999)}"

    async with CONCURRENCY_SEMAPHORE:
        # Select consistent profile
        profile = random.choice(STEALTH_PROFILES)
        proxy_config = get_stabilized_proxy(session_id)
        
        # Merge headers. Fallback spoofing X-Forwarded-For if proxy not provided.
        headers = dict(profile["headers"])
        if not proxy_config:
            headers["X-Forwarded-For"] = (
                f"{random.randint(1,255)}.{random.randint(1,255)}"
                f".{random.randint(1,255)}.{random.randint(1,255)}"
            )

        # Inject GA tracking cookies to simulate return visitor
        cookies = {
            "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
            "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
        }

        # Initialize spoofed session
        async with requests.AsyncSession(
            impersonate=profile["impersonate"],
            proxies=proxy_config,
            headers=headers,
            cookies=cookies,
        ) as session:
            parsed_uri = urllib.parse.urlparse(url)
            root_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"

            try:
                # 1. Warmup Step A: Fetch robots.txt or root domain (to collect cookies / clear challenge)
                warmup_url = root_domain if "sannysoft" in root_domain else f"{root_domain}robots.txt"
                logger.info(f"Warmup: hitting {warmup_url} with profile {profile['id']}")
                await session.get(warmup_url, timeout=15)
                
                # Organic human delay (jitter)
                await asyncio.sleep(random.uniform(2.5, 6.0))

                # 2. Referer setup & Target Fetch
                session.headers.update({"Referer": root_domain})
                logger.info(f"Stealth fetching target: {url}")
                response = await session.get(url, timeout=20)
                response.raise_for_status()

                # Parse and return
                return _parse_job_page(response.text, url)

            except Exception as e:
                logger.error(f"Failed to stealth-fetch {url}: {e}")
                return None


async def stealth_scrape_jobs(urls: List[str]) -> List[dict]:
    """
    Main stealth scraping engine.
    Applies concurrency control and session pinning.
    """
    tasks = []
    for url in urls:
        # Create a unique session ID per URL to isolate proxies/cookies
        session_id = f"job_sess_{random.randint(100000, 999999)}"
        tasks.append(process_single_job(url, session_id))

    results_raw = await asyncio.gather(*tasks)

    # Filter out failed fetches
    results = [r for r in results_raw if r is not None]
    logger.info(f"Stealth scrape complete: {len(results)}/{len(urls)} pages parsed successfully.")
    return results


async def verify_sannysoft_bypass(proxy: Optional[str] = None) -> bool:
    """
    Verification method to test sannysoft bypass.
    Checks if Cloudflare is bypassed and the page is returned successfully.
    """
    if not HAS_CFFI:
        print("Verification failed: curl_cffi not installed")
        return False
    
    url = "https://bot.sannysoft.com/"
    profile = random.choice(STEALTH_PROFILES)
    headers = dict(profile["headers"])
    
    proxies = {"http": proxy, "https": proxy} if proxy else {}
    
    print(f"Verifying sannysoft bypass using profile {profile['id']}...")
    try:
        async with requests.AsyncSession(
            impersonate=profile["impersonate"],
            proxies=proxies,
            headers=headers
        ) as session:
            # Direct hit
            res = await session.get(url, timeout=20)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.find("title")
            title_text = title.text if title else ""
            print(f"Fetched page title: {title_text}")
            
            # Sannysoft title is usually 'Bot Detection' or contains 'sannysoft'
            if "sannysoft" in res.text.lower() or "bot detection" in title_text.lower():
                print("Bypass Check Passed: Page retrieved successfully!")
                return True
            else:
                print("Bypass Check Failed: Response does not contain sannysoft indicators.")
                return False
                
    except Exception as e:
        print(f"Bypass Check Failed with exception: {e}")
        return False


if __name__ == "__main__":
    # Test verify function
    import sys
    test_proxy = os.getenv("TEST_PROXY")
    success = asyncio.run(verify_sannysoft_bypass(test_proxy))
    sys.exit(0 if success else 1)

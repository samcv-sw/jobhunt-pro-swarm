import asyncio
import random
import logging
import urllib.parse
from typing import List, Dict, Optional
import os
import time
import json

try:
    from curl_cffi import requests
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Parse proxies from env. Supports comma-separated list.
PROXY_LIST = [p.strip() for p in os.getenv("RESIDENTIAL_PROXIES", "").split(",") if p.strip()]

# Automatically aligned curl_cffi impersonate profiles to avoid runtime ValueError exceptions.
STEALTH_PROFILES = [
    {
        "id": "chrome120",
        "impersonate": "chrome120",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    {
        "id": "chrome124",
        "impersonate": "chrome124",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    },
    {
        "id": "firefox120",
        "impersonate": "firefox120",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    },
    {
        "id": "safari18_0",
        "impersonate": "safari18_0",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
    }
]


def get_stabilized_proxy(session_id: str = "default") -> dict:
    """
    Selects a proxy based on session_id to maintain IP pinning.
    If no user-configured residential proxies exist, falls back to the dynamic 
    elite proxy harvester from core/stealth.py to avoid unproxied requests.
    """
    if not PROXY_LIST:
        try:
            from core.stealth import stealth
            harvested = stealth.get_random_proxy()
            if harvested:
                logger.info(f"Using harvested fallback proxy: {harvested}")
                return {"http": harvested, "https": harvested}
        except Exception as e:
            logger.warning(f"Failed to fetch harvested proxy: {e}")
        return {}

    proxy_str = PROXY_LIST[0]
    
    # Check if we have a single backconnect proxy (inject session ID into username)
    if len(PROXY_LIST) == 1 and "@" in proxy_str and ("session-" not in proxy_str):
        parsed = urllib.parse.urlsplit(proxy_str)
        if parsed.username and parsed.password:
            new_username = f"{parsed.username}-session-{session_id}"
            port_part = f":{parsed.port}" if parsed.port else ""
            netloc = f"{new_username}:{parsed.password}@{parsed.hostname}{port_part}"
            reconstructed = urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
            return {"http": reconstructed, "https": reconstructed}

    # Pin to a specific proxy in the list using hash of session_id
    idx = hash(session_id) % len(PROXY_LIST)
    selected_proxy = PROXY_LIST[idx]
    return {"http": selected_proxy, "https": selected_proxy}


def _get_headers_for_profile(profile: dict, root_domain: str) -> dict:
    """
    Dynamically generates standard headers for the chosen browser profile.
    Ensures HTTP/2 pseudo-headers and browser-specific headers match the user agent.
    """
    parsed = urllib.parse.urlparse(root_domain)
    host = parsed.netloc
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "User-Agent": profile["user_agent"],
        "Host": host,
    }
    
    # Profile-specific adjustments
    impersonate_str = profile["impersonate"]
    if "chrome" in impersonate_str:
        headers["Sec-CH-UA"] = f'"Google Chrome";v="{impersonate_str[6:]}", "Chromium";v="{impersonate_str[6:]}", "Not_A Brand";v="24"'
        headers["Sec-CH-UA-Mobile"] = "?0"
        headers["Sec-CH-UA-Platform"] = '"Windows"'
        headers["Connection"] = "keep-alive"
    elif "firefox" in impersonate_str:
        headers["Accept-Language"] = "en-US,en;q=0.5"
        headers["Connection"] = "keep-alive"
    elif "safari" in impersonate_str:
        # Safari on macOS does not send Connection: keep-alive or Sec-CH-UA client hints
        headers.pop("Connection", None)
        headers["Accept-Language"] = "en-US,en;q=0.9,ar-XM;q=0.8"
        
    return headers


def _parse_job_page(html: str, source_url: str) -> dict | None:
    """
    Parses job page HTML. Tries JSON-LD first, then BeautifulSoup CSS selectors fallback.
    Returns None if parsing fails or Cloudflare block screen is detected.
    """
    if not html:
        return None
        
    # Check for common bot blocking/Cloudflare strings
    is_blocked = any(term in html.lower() for term in [
        "just a moment", "attention required", "turnstile", "ray id", "ddg-captcha", "perimeterx", "datadome"
    ])
    if is_blocked:
        logger.error(f"Anti-bot block screen detected on page: {source_url}")
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Try extracting Schema.org JobPosting JSON-LD (Standard for modern job portals)
        json_ld_tags = soup.find_all("script", type="application/ld+json")
        for tag in json_ld_tags:
            try:
                data = json.loads(tag.string or "")
                if isinstance(data, list):
                    item = data[0]
                else:
                    item = data
                    
                if item.get("@type") == "JobPosting":
                    title = item.get("title")
                    company_data = item.get("hiringOrganization")
                    company = ""
                    if isinstance(company_data, dict):
                        company = company_data.get("name")
                    elif isinstance(company_data, str):
                        company = company_data
                        
                    desc = item.get("description", "")
                    # Strip HTML from description text
                    desc_text = BeautifulSoup(desc, "html.parser").get_text(separator=" ", strip=True)
                    
                    if title:
                        return {
                            "title": title.strip(),
                            "url": source_url,
                            "company": company.strip() if company else None,
                            "description_snippet": desc_text[:500].strip(),
                        }
            except Exception:
                continue
                
        # 2. BeautifulSoup CSS Selectors Fallback
        title = "Unknown Position"
        for selector in [
            "h1.job-title", "h1.title", "h1",
            ".jobsearch-JobInfoHeader-title", ".job-title", ".title"
        ]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    title = text
                    break
                    
        # Fallback to document title if still unknown
        if title == "Unknown Position" or not title:
            title_el = soup.find("title")
            if title_el:
                title = title_el.get_text(strip=True)
                # Clean up typical title suffix
                for sep in [" - ", " | "]:
                    if sep in title:
                        title = title.split(sep)[0]

        company = None
        for selector in [
            ".company-name", ".company", "[class*='company']",
            ".jobsearch-CompanyInfoWithoutHeaderImage", ".jobsearch-InlineCompanyRating"
        ]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    company = text
                    break
                    
        desc_el = (
            soup.select_one("#jobDescriptionText") 
            or soup.select_one(".job-description") 
            or soup.select_one(".description")
            or soup.select_one("body")
        )
        description_snippet = desc_el.get_text(separator=" ", strip=True)[:500] if desc_el else ""

        return {
            "title": title.strip(),
            "url": source_url,
            "company": company.strip() if company else None,
            "description_snippet": description_snippet.strip(),
        }
    except Exception as e:
        logger.error(f"Parsing error for {source_url}: {e}")
        return None


async def _fetch_with_browser_fallback(url: str, proxy: Optional[str] = None) -> str:
    """
    Fallback to browser automation engines (Nodriver or Camoufox) if HTTP requests fail.
    Inherits Bezier mouse movement and WebGL/Canvas spoofing natively.
    """
    # 1. Try Camoufox (highest stealth Firefox C++ modification)
    try:
        from core.stealth import ApexCamoufoxFallback
        logger.info(f"Triggering Camoufox browser fallback for {url}")
        html = await ApexCamoufoxFallback.get_page_content(url, proxy=proxy)
        if html and len(html) > 1000 and "just a moment" not in html.lower():
            return html
    except Exception as e:
        logger.warning(f"Camoufox fallback failed: {e}")
        
    # 2. Try Nodriver (Chrome-based automation)
    try:
        from core.stealth import NodriverFallback
        logger.info(f"Triggering Nodriver browser fallback for {url}")
        html = await NodriverFallback.get_page_content(url)
        if html and len(html) > 1000 and "just a moment" not in html.lower():
            return html
    except Exception as e:
        logger.warning(f"Nodriver fallback failed: {e}")
        
    return ""


async def process_single_job(url: str, session_id: Optional[str] = None, session: Optional[requests.AsyncSession] = None) -> dict | None:
    """
    Fetches and parses a single job URL.
    Uses curl_cffi AsyncSession with TLS/HTTP2 impersonation.
    Falls back to headless browsers (nodriver/camoufox) if a block screen is encountered.
    """
    if not HAS_CFFI:
        logger.warning("curl_cffi not installed! Bypassing is severely limited.")
        html = await _fetch_with_browser_fallback(url)
        return _parse_job_page(html, url)

    if not session_id:
        session_id = f"sess_{random.randint(100000, 999999)}"

    # Select profile and proxy configuration
    profile = random.choice(STEALTH_PROFILES)
    proxy_config = get_stabilized_proxy(session_id)
    
    parsed_uri = urllib.parse.urlparse(url)
    root_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
    headers = _get_headers_for_profile(profile, root_domain)

    # Use existing session or create a new one
    close_session = False
    if session is None:
        cookies = {
            "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
            "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
        }
        session = requests.AsyncSession(
            impersonate=profile["impersonate"],
            proxies=proxy_config,
            headers=headers,
            cookies=cookies,
        )
        close_session = True

    try:
        is_warmed_up = getattr(session, "_warmed_up", False)
        if not is_warmed_up:
            warmup_url = root_domain
            logger.info(f"Warmup: hitting root domain {warmup_url} with profile {profile['id']}")
            warmup_headers = headers.copy()
            warmup_headers["Sec-Fetch-Site"] = "none"
            await session.get(warmup_url, headers=warmup_headers, timeout=15)
            session._warmed_up = True
            
            # Organic delay before target fetch
            await asyncio.sleep(random.uniform(2.5, 5.0))

        # Target Fetch Setup
        session.headers.update({
            "Referer": root_domain,
            "Sec-Fetch-Site": "same-origin"
        })
        
        logger.info(f"Stealth fetching target: {url}")
        response = await session.get(url, timeout=20)
        
        # Parse result and check for block screen
        parsed_result = _parse_job_page(response.text, url)
        
        # If we failed to parse or got a block screen, try browser fallback
        if parsed_result is None or response.status_code in [403, 429]:
            logger.warning(f"Detection triggered on {url}. Initiating browser automation fallback...")
            proxy_str = proxy_config.get("https") or proxy_config.get("http")
            html = await _fetch_with_browser_fallback(url, proxy=proxy_str)
            return _parse_job_page(html, url)
            
        return parsed_result

    except Exception as e:
        logger.error(f"Failed to fetch {url} via curl_cffi: {e}. Trying browser fallback...")
        proxy_str = proxy_config.get("https") or proxy_config.get("http")
        html = await _fetch_with_browser_fallback(url, proxy=proxy_str)
        return _parse_job_page(html, url)
        
    finally:
        if close_session:
            await session.close()


async def stealth_scrape_jobs(urls: List[str]) -> List[dict]:
    """
    Main stealth scraping engine.
    Applies request shuffling, decoy requests, and session reuse to prevent pattern detection.
    """
    if not urls:
        return []

    # Group URLs by domain to reuse sessions and cookies
    urls_by_domain = {}
    for url in urls:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc
        urls_by_domain.setdefault(domain, []).append(url)

    results = []
    
    # Process domains sequentially to avoid simultaneous requests on different domains
    for domain, domain_urls in urls_by_domain.items():
        logger.info(f"Processing {len(domain_urls)} target URLs for domain {domain}")
        
        # Shuffle URLs to avoid predictable crawl paths
        random.shuffle(domain_urls)
        
        session_id = f"job_sess_{random.randint(100000, 999999)}"
        profile = random.choice(STEALTH_PROFILES)
        proxy_config = get_stabilized_proxy(session_id)
        
        # Re-use a single session for all requests to this domain
        if HAS_CFFI:
            root_url = f"https://{domain}/"
            headers = _get_headers_for_profile(profile, root_url)
            cookies = {
                "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
                "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
            }
            session = requests.AsyncSession(
                impersonate=profile["impersonate"],
                proxies=proxy_config,
                headers=headers,
                cookies=cookies,
            )
        else:
            session = None

        try:
            for i, url in enumerate(domain_urls):
                res = await process_single_job(url, session_id, session=session)
                if res:
                    results.append(res)
                
                # Jitter delay between requests on the same domain
                if i < len(domain_urls) - 1:
                    delay = random.uniform(4.0, 9.0)
                    logger.info(f"Sleeping for {delay:.2f}s before next request...")
                    await asyncio.sleep(delay)
        finally:
            if session:
                await session.close()
                
    logger.info(f"Stealth scrape complete: {len(results)}/{len(urls)} pages parsed successfully.")
    return results


async def verify_sannysoft_bypass(proxy: Optional[str] = None) -> bool:
    """
    Verification method to test sannysoft bypass.
    """
    if not HAS_CFFI:
        print("Verification failed: curl_cffi not installed")
        return False
    
    url = "https://bot.sannysoft.com/"
    profile = random.choice(STEALTH_PROFILES)
    headers = _get_headers_for_profile(profile, url)
    proxies = {"http": proxy, "https": proxy} if proxy else {}
    
    print(f"Verifying sannysoft bypass using profile {profile['id']}...")
    try:
        async with requests.AsyncSession(
            impersonate=profile["impersonate"],
            proxies=proxies,
            headers=headers
        ) as session:
            res = await session.get(url, timeout=20)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.find("title")
            title_text = title.text if title else ""
            print(f"Fetched page title: {title_text}")
            
            if "sannysoft" in res.text.lower() or "bot detection" in title_text.lower() or "antibot" in title_text.lower():
                print("Bypass Check Passed: Page retrieved successfully!")
                return True
            else:
                print("Bypass Check Failed: Response does not contain sannysoft indicators.")
                return False
    except Exception as e:
        print(f"Bypass Check Failed with exception: {e}")
        return False


if __name__ == "__main__":
    import sys
    test_proxy = os.getenv("TEST_PROXY")
    success = asyncio.run(verify_sannysoft_bypass(test_proxy))
    sys.exit(0 if success else 1)

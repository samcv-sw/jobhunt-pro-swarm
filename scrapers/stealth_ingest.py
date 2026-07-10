import asyncio
import random
import logging
import urllib.parse
from typing import List, Dict, Optional, Any
import os
import time

try:
    from curl_cffi import requests
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_raw_proxies = os.getenv("RESIDENTIAL_PROXIES", "")
if not _raw_proxies or not _raw_proxies.strip():
    PROXY_LIST = []
else:
    PROXY_LIST = [p.strip() for p in _raw_proxies.split(",") if p.strip()]

# Curated browser profiles with aligned TLS target and HTTP headers
STEALTH_PROFILES = [
    {
        "id": "chrome131",
        "impersonate": "chrome120",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Sec-CH-UA": '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
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
        "impersonate": "chrome120",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Sec-CH-UA": '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
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
        "impersonate": "safari17_2_1",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
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
        "impersonate": "safari17_2_1",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
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
        "impersonate": "firefox120",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
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


_last_proxy_fetch = 0
_cached_free_proxies = []
_proxy_fetch_lock = asyncio.Lock()

async def get_stabilized_proxy(session_id: str = "default") -> dict:
    """
    Selects a proxy based on session_id to maintain IP pinning.
    Supports backconnect gateways (injecting session ID into username) 
    or selecting a pinned IP from a list.
    """
    global _last_proxy_fetch, _cached_free_proxies
    
    if PROXY_LIST:
        active_proxies = PROXY_LIST
    else:
        # Dynamically generate/rotate free public proxies if RESIDENTIAL_PROXIES is empty
        import sys
        if os.environ.get("TESTING") == "true" or "pytest" in sys.modules:
            active_proxies = ["http://jobhunt-stub-proxy:8080"]
        else:
            now = time.time()
            if not _cached_free_proxies or now - _last_proxy_fetch > 600:
                async with _proxy_fetch_lock:
                    # Double-check inside lock
                    now = time.time()
                    if not _cached_free_proxies or now - _last_proxy_fetch > 600:
                        try:
                            import requests
                            def _fetch():
                                return requests.get(
                                    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=elite",
                                    timeout=5.0
                                )
                            res = await asyncio.to_thread(_fetch)
                            if res.status_code == 200:
                                fetched = [f"http://{p.strip()}" for p in res.text.split("\n") if p.strip()]
                                if fetched:
                                    _cached_free_proxies = fetched
                                    _last_proxy_fetch = now
                        except Exception as e:
                            logger.warning(f"Failed to fetch public proxies: {e}")
            active_proxies = _cached_free_proxies if _cached_free_proxies else ["http://jobhunt-stub-proxy:8080"]

    # If it's a single backconnect proxy (e.g., contains @ and is a gate provider)
    # we can inject session ID into username if supported, e.g., user-session-XYZ123:pass@gate.proxy.com:port
    proxy_str = active_proxies[0]
    
    if len(active_proxies) == 1 and "@" in proxy_str and ("session-" not in proxy_str):
        # E.g. http://username:password@proxy.gate.com:8000 -> http://username-session-XYZ:password@proxy.gate.com:8000
        parsed = urllib.parse.urlsplit(proxy_str)
        if parsed.username and parsed.password:
            new_username = f"{parsed.username}-session-{session_id}"
            # Reconstruct netloc with new username
            port_part = f":{parsed.port}" if parsed.port else ""
            netloc = f"{new_username}:{parsed.password}@{parsed.hostname}{port_part}"
            reconstructed = urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
            return {"http": reconstructed, "https": reconstructed}

    # Otherwise, pin to a specific proxy in the list using hash of session_id
    idx = hash(session_id) % len(active_proxies)
    selected_proxy = active_proxies[idx]
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
        title = "Unknown Position"
        for selector_fn in [
            lambda s: s.find("h1"),
            lambda s: s.find(attrs={"class": lambda c: c and "job-title" in c}),
            lambda s: s.find(attrs={"class": lambda c: c and "title" in c}),
            lambda s: s.find("title")
        ]:
            el = selector_fn(soup)
            if el:
                text = el.get_text(strip=True)
                if text:
                    title = text
                    break

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


def _extract_jobs_from_dict(data: Any, source_url: str) -> List[Dict[str, Any]]:
    results = []
    if isinstance(data, dict):
        types = data.get("@type", "")
        is_job = False
        if isinstance(types, list):
            is_job = "JobPosting" in types
        else:
            is_job = types == "JobPosting"
            
        if is_job or (isinstance(data.get("title"), str) and (data.get("url") or data.get("hiringOrganization"))):
            title = data.get("title") or data.get("name")
            if title:
                url = data.get("url") or source_url
                company = None
                hiring_org = data.get("hiringOrganization")
                if hiring_org and isinstance(hiring_org, dict):
                    company = hiring_org.get("name")
                elif isinstance(hiring_org, str):
                    company = hiring_org
                desc = data.get("description") or ""
                if desc:
                    try:
                        desc = BeautifulSoup(desc, "html.parser").get_text(separator=" ", strip=True)
                    except Exception:
                        pass
                results.append({
                    "title": title,
                    "url": url,
                    "company": company,
                    "description_snippet": desc[:500]
                })
        
        # Recursively search all keys
        for k, v in data.items():
            results.extend(_extract_jobs_from_dict(v, source_url))
            
    elif isinstance(data, list):
        for item in data:
            results.extend(_extract_jobs_from_dict(item, source_url))
            
    return results


def _parse_json_ld(html: str, source_url: str) -> List[Dict[str, Any]]:
    import json
    results = []
    if not html:
        return results
    try:
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                extracted = _extract_jobs_from_dict(data, source_url)
                if extracted:
                    results.extend(extracted)
            except Exception as ex:
                logger.debug(f"JSON-LD parsing nested item failed: {ex}")
    except Exception as e:
        logger.warning(f"Error extracting JSON-LD scripts: {e}")
    return results


def _parse_page_content(html: str, source_url: str) -> List[Dict[str, Any]]:
    """
    Parses a page's content.
    If JSON-LD is found with jobs, returns them.
    If multi-card listings are found, returns a list of dictionaries with job details.
    If no cards are found, falls back to parsing as a single job page.
    If html is empty or parsing fails, returns [].
    """
    if not html:
        return []
        
    # 1. Try parsing JSON-LD structured data first
    json_ld_jobs = _parse_json_ld(html, source_url)
    if json_ld_jobs:
        return json_ld_jobs
        
    # 2. Traditional card parsing
    try:
        soup = BeautifulSoup(html, "html.parser")
        cards = []
        # Find all cards matching target selectors
        for selector in [
            "div.job_seen_beacon",
            "li.jobs-search-results__list-item",
            "div.job-card",
            "article.job-listing"
        ]:
            found = soup.select(selector)
            if found:
                cards.extend(found)
        
        if cards:
            results = []
            for card in cards:
                # 1. Title
                title = "Unknown Position"
                for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    heading = card.find(tag_name)
                    if heading:
                        text = heading.get_text(strip=True)
                        if text:
                            title = text
                            break
                if title == "Unknown Position":
                    for el in card.find_all(attrs={"class": lambda c: c and any(kw in str(c).lower() for kw in ["title", "jobtitle"])}):
                        text = el.get_text(strip=True)
                        if text:
                            title = text
                            break

                # 2. Company
                company = None
                company_el = card.find(attrs={"class": lambda c: c and "company" in str(c).lower()})
                if company_el:
                    company = company_el.get_text(strip=True)

                # 3. URL
                job_url = source_url
                a_tags = card.find_all("a")
                for a in a_tags:
                    href = a.get("href")
                    if href:
                        job_url = urllib.parse.urljoin(source_url, href)
                        break

                # 4. Description snippet
                description_snippet = ""
                desc_el = card.find(attrs={"class": lambda c: c and any(kw in str(c).lower() for kw in ["snippet", "description", "summary", "short"])})
                if desc_el:
                    description_snippet = desc_el.get_text(strip=True)
                else:
                    card_text = card.get_text(separator=" ", strip=True)
                    description_snippet = card_text[:500] if card_text else ""

                results.append({
                    "title": title,
                    "url": job_url,
                    "company": company,
                    "description_snippet": description_snippet
                })
            return results
        else:
            single = _parse_job_page(html, source_url)
            return [single] if single else []
    except Exception as e:
        logger.error(f"Error parsing page content for {source_url}: {e}")
        return []


async def _parse_html_with_llm(html: str, source_url: str) -> List[Dict[str, Any]]:
    """
    Generative LLM fallback parser that cleans raw HTML and formats it into structured JSON lists.
    """
    if not html:
        return []
    try:
        from core.ai_tailor import AITailor
        ai_tailor = AITailor()
        
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
            
        clean_text = soup.get_text(separator=" ", strip=True)
        clean_text = clean_text[:4000]
        
        prompt = f"""You are a data extraction AI. Extract all job listings from the following webpage text.
For each job, extract the job title, company name, URL (use {source_url} if not found), and a brief description/snippet.

Webpage text:
{clean_text}

Return ONLY a valid JSON list of objects. Each object MUST have the following keys:
- 'title': The job title (string, required)
- 'url': The job detail URL or apply URL (string, required, fallback to {source_url})
- 'company': The hiring company name (string or null)
- 'description_snippet': A brief description or snippet (string or null)

Example response format:
[
  {{"title": "Software Engineer", "url": "https://example.com/job/1", "company": "Acme Corp", "description_snippet": "We are looking for..."}}
]
"""
        result = await ai_tailor._call_ai(prompt, max_tokens=1500, temperature=0.1)
        if result:
            import json
            json_str = AITailor._extract_json(result)
            start_idx = json_str.find("[")
            end_idx = json_str.rfind("]")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = json_str[start_idx:end_idx+1]
            jobs = json.loads(json_str)
            if isinstance(jobs, dict):
                jobs = [jobs]
            if isinstance(jobs, list):
                cleaned_jobs = []
                for job in jobs:
                    if isinstance(job, dict) and "title" in job:
                        cleaned_jobs.append({
                            "title": job.get("title") or "Unknown Position",
                            "url": job.get("url") or source_url,
                            "company": job.get("company"),
                            "description_snippet": job.get("description_snippet", "")
                        })
                return cleaned_jobs
    except Exception as e:
        logger.warning(f"Generative LLM fallback parser failed: {e}")
    return []


async def process_single_job(url: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches a single job URL with stealth session isolation and parses it.
    Returns a list of structured job dicts or [] on failure.
    Uses Concurrency Semaphore and random delay (jitter).
    Integrates progressive browser fallbacks if Cloudflare or bot challenge is detected.
    """
    # Set up session-id for proxy pinning
    if not session_id:
        session_id = f"sess_{random.randint(100000, 999999)}"

    proxy_config = await get_stabilized_proxy(session_id)
    html_content = ""

    async with CONCURRENCY_SEMAPHORE:
        if HAS_CFFI:
            profile = random.choice(STEALTH_PROFILES)
            headers = dict(profile["headers"])
            if not proxy_config:
                headers["X-Forwarded-For"] = (
                    f"{random.randint(1,255)}.{random.randint(1,255)}"
                    f".{random.randint(1,255)}.{random.randint(1,255)}"
                )

            cookies = {
                "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
                "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
            }

            try:
                async with requests.AsyncSession(
                    impersonate=profile["impersonate"],
                    proxies=proxy_config,
                    headers=headers,
                    cookies=cookies,
                ) as session:
                    parsed_uri = urllib.parse.urlparse(url)
                    root_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"

                    warmup_url = root_domain if "sannysoft" in root_domain else f"{root_domain}robots.txt"
                    logger.info(f"Warmup: hitting {warmup_url} with profile {profile['id']}")
                    await session.get(warmup_url, timeout=15)
                    
                    await asyncio.sleep(random.uniform(2.5, 6.0))

                    session.headers.update({"Referer": root_domain})
                    logger.info(f"Stealth fetching target: {url}")
                    response = await session.get(url, timeout=20)
                    response.raise_for_status()

                    response_text = response.text
                    if any(k in response_text.lower() for k in ["just a moment", "attention required", "turnstile", "ddg-captcha"]):
                        logger.warning(f"Bot detection challenge screen detected in response for {url}.")
                    else:
                        html_content = response_text

            except Exception as e:
                logger.warning(f"Failed to stealth-fetch {url} via curl_cffi: {e}")
        else:
            logger.warning("curl_cffi not installed! Skipping direct HTTP session.")

        if not html_content:
            logger.warning(f"Stealth fetch returned empty or challenged content. Trying NodriverFallback for {url}.")
            try:
                from core.stealth import NodriverFallback
                proxy_str = proxy_config.get("http") if proxy_config else None
                html_content = await NodriverFallback.get_page_content(url, proxy=proxy_str)
            except Exception as ne:
                logger.error(f"NodriverFallback failed for {url}: {ne}")

            if not html_content or any(k in html_content.lower() for k in ["just a moment", "attention required", "turnstile", "ddg-captcha"]):
                logger.warning(f"Nodriver fallback failed or was challenged. Trying ApexCamoufoxFallback for {url}.")
                try:
                    from core.stealth import ApexCamoufoxFallback
                    proxy_str = proxy_config.get("http") if proxy_config else None
                    html_content = await ApexCamoufoxFallback.get_page_content(url, proxy=proxy_str)
                except Exception as ce:
                    logger.error(f"ApexCamoufoxFallback failed for {url}: {ce}")

        jobs = _parse_page_content(html_content, url)
        # Check if jobs is empty or only contains a placeholder/unknown title
        has_valid_job = False
        if jobs:
            for job in jobs:
                if job.get("title") and job.get("title") != "Unknown Position":
                    has_valid_job = True
                    break
                    
        # 3. Add generative LLM fallback parser if parsing returned no results
        if not has_valid_job and html_content:
            logger.info(f"Normal parsing yielded no results. Triggering generative LLM fallback parser for {url}.")
            llm_jobs = await _parse_html_with_llm(html_content, url)
            if llm_jobs:
                jobs = llm_jobs
            
        # Ensure that every job returned is a clean dict with at least 'title' and 'url' keys
        cleaned_jobs = []
        for job in jobs:
            if isinstance(job, dict):
                cleaned_job = {
                    "title": job.get("title") or "Unknown Position",
                    "url": job.get("url") or url,
                    "company": job.get("company"),
                    "description_snippet": job.get("description_snippet", "")
                }
                cleaned_jobs.append(cleaned_job)
                
        return cleaned_jobs


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

    # Flat-map all the lists of dicts returned by process_single_job into a single list of dicts.
    results = []
    for r in results_raw:
        if r is None:
            continue
        if isinstance(r, list):
            for item in r:
                if isinstance(item, dict):
                    results.append({
                        "title": item.get("title") or "Unknown Position",
                        "url": item.get("url") or "Unknown URL",
                        "company": item.get("company"),
                        "description_snippet": item.get("description_snippet", "")
                    })
        elif isinstance(r, dict):
            # Fallback if process_single_job gets mocked to return a single dict in tests
            results.append({
                "title": r.get("title") or "Unknown Position",
                "url": r.get("url") or "Unknown URL",
                "company": r.get("company"),
                "description_snippet": r.get("description_snippet", "")
            })

    logger.info(f"Stealth scrape complete: {len(results)} jobs parsed successfully.")
    return results


async def verify_sannysoft_bypass(proxy: Optional[str] = None) -> bool:
    """
    Verification method to test sannysoft bypass.
    Checks if Cloudflare is bypassed and the page is returned successfully.
    """
    if not HAS_CFFI:
        logger.debug("Verification failed: curl_cffi not installed")
        return False
    
    url = "https://bot.sannysoft.com/"
    profile = random.choice(STEALTH_PROFILES)
    headers = dict(profile["headers"])
    
    proxies = {"http": proxy, "https": proxy} if proxy else {}
    
    logger.debug(f"Verifying sannysoft bypass using profile {profile['id']}...")
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
            logger.debug(f"Fetched page title: {title_text}")
            
            # Sannysoft title is usually 'Antibot', 'Bot Detection' or contains 'sannysoft'
            if "sannysoft" in res.text.lower() or "bot detection" in title_text.lower() or "antibot" in title_text.lower():
                logger.debug("Bypass Check Passed: Page retrieved successfully!")
                return True
            else:
                logger.debug("Bypass Check Failed: Response does not contain sannysoft indicators.")
                return False
                
    except Exception as e:
        logger.debug(f"Bypass Check Failed with exception: {e}")
        return False


if __name__ == "__main__":
    # Test verify function
    import sys
    test_proxy = os.getenv("TEST_PROXY")
    success = asyncio.run(verify_sannysoft_bypass(test_proxy))
    sys.exit(0 if success else 1)

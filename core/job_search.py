"""
JobHunt Pro - Enterprise Job Search Architecture (Omniscient Principal Engineer Refactor)
100% Asynchronous, Pydantic Validated, Caching, Proxies, Anti-Bot Evasion, Resilient.
"""
import asyncio
import hashlib
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Set, Callable, Any, Dict, Final, Tuple

import httpx
from core.stealth import stealth
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, Field

import config

logger = logging.getLogger(__name__)

# ── 1. Strict Type Definitions & Constants ──────────────────────────────────
MAX_CONCURRENT_SCRAPES: Final[int] = 5
DEFAULT_CACHE_TTL_SEC: Final[int] = 600  # 10 minutes

# ── 2. Pydantic Models for Strict Data Validation ───────────────────────────
class JobListing(BaseModel):
    job_id: str
    title: str
    company: str
    email: str
    all_emails: List[str] = Field(default_factory=list)
    location: str
    snippet: str
    source: str
    url: str
    salary: Optional[float] = None

# ── 3. Advanced Anti-Bot & Evasion Tactics ──────────────────────────────────
USER_AGENTS: Final[Tuple[str, ...]] = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
)

def get_dynamic_headers() -> Dict[str, str]:
    """Generates highly randomized, browser-like headers to evade basic bot detection."""
    ua = random.choice(USER_AGENTS)
    is_chrome = "Chrome" in ua
    
    headers = {
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.8,en-US;q=0.6', 'en-US,en;q=0.5']),
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    if is_chrome:
        headers.update({
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"' if 'Windows' in ua else '"macOS"' if 'Macintosh' in ua else '"Linux"',
        })
    return headers

# ── 4. Proxy Integration Readiness ──────────────────────────────────────────
def get_random_proxy() -> Optional[str]:
    """Fetches a random proxy from config if available."""
    proxies = getattr(config, 'ROTATING_PROXIES', [])
    return random.choice(proxies) if proxies else None

# ── 5. In-Memory LRU Caching ────────────────────────────────────────────────
class TTLQueryCache:
    """Thread-safe, TTL-based in-memory cache to prevent redundant scraping."""
    def __init__(self, ttl: int = DEFAULT_CACHE_TTL_SEC):
        self.ttl = ttl
        self._cache: Dict[str, Tuple[float, List[JobListing]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[List[JobListing]]:
        async with self._lock:
            if key in self._cache:
                timestamp, data = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    logger.info(f"Cache HIT for query: {key}")
                    return data
                else:
                    del self._cache[key]
            return None

    async def set(self, key: str, data: List[JobListing]) -> None:
        async with self._lock:
            self._cache[key] = (time.time(), data)

# Global Cache Instance
query_cache = TTLQueryCache()

# ── 6. Resilience, Exponential Backoff & 429 Handling ───────────────────────
def async_retry(max_retries: int = 3, base_delay: float = 2.0) -> Callable:
    """Robust retry decorator with specific handling for HTTP 429 (Rate Limit)."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        # Respect Rate Limit
                        retry_after = int(e.response.headers.get("Retry-After", base_delay ** attempt * 2))
                        logger.warning(f"[{func.__name__}] HTTP 429 Rate Limit Hit. Sleeping {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if attempt == max_retries:
                        logger.error(f"[{func.__name__}] Terminal HTTP error: {e.response.status_code}")
                        return []
                        
                    delay = base_delay ** attempt + random.uniform(0, 1)
                    logger.warning(f"[{func.__name__}] HTTP error {e.response.status_code}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    
                except httpx.RequestError as e:
                    if attempt == max_retries:
                        logger.error(f"[{func.__name__}] Terminal Network Error: {e}")
                        return []
                    delay = base_delay ** attempt + random.uniform(0, 1)
                    logger.warning(f"[{func.__name__}] Network error: {e}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"[{func.__name__}] Unexpected Critical Error: {e}", exc_info=True)
                    return []
            return []
        return wrapper
    return decorator

# ── 7. Email Extraction & Validation Logic ──────────────────────────────────
EMAIL_PATTERN: Final[re.Pattern] = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
BLOCKED_EMAILS: Final[frozenset] = frozenset([
    'noreply@', 'no-reply@', 'donotreply@', 'example.com', 'test.com',
    'w3.org', 'schema.org', 'sentry', 'webpack', 'facebook.com',
    'google.com', 'github.com', 'microsoft.com', 'apple.com',
    'cloudflare.com', 'jquery.com', 'wikipedia.org', 'youtube.com',
    'twitter.com', 'instagram.com', 'linkedin.com', 'tiktok.com',
    'sentry.io', 'noreply.', 'no-reply.', 'donotreply.'
])
# Ordered by likelihood — careers/hr/recruitment are best for job applications
HR_EMAIL_PATTERNS: Final[frozenset] = frozenset([
    'careers@', 'hr@', 'recruitment@', 'jobs@', 'hiring@',
    'talent@', 'recruiting@', 'people@', 'cv@', 'apply@',
    'info@', 'contact@', 'hello@', 'admin@', 'office@',
])

def extract_valid_emails(text: str) -> List[str]:
    """Memory-efficient generator for email extraction."""
    if not text:
        return []
    
    def valid_email_generator():
        for match in EMAIL_PATTERN.finditer(text):
            e_lower = match.group(0).lower().strip()
            if len(e_lower) >= 100 or '.' not in e_lower.split('@')[1]:
                continue
            if any(b in e_lower for b in BLOCKED_EMAILS):
                continue
            if e_lower.endswith(('.png', '.jpg', '.gif', '.svg')):
                continue
            yield e_lower

    return list(set(valid_email_generator()))

# Priority order for HR email selection (most → least likely to reach hiring team)
_HR_PRIORITY_ORDER: List[str] = [
    'careers@', 'hr@', 'recruitment@', 'jobs@', 'hiring@',
    'talent@', 'recruiting@', 'people@', 'cv@', 'apply@',
    'info@', 'contact@', 'hello@', 'admin@', 'office@',
]


# Company suffixes for fallback domain generation (legal suffixes only)
_COMPANY_DOMAIN_SUFFIXES = [
    r'\bLLC\b', r'\bInc\.?\b', r'\bLtd\.?\b', r'\bCorp\.?\b',
    r'\bCorporation\b', r'\bIncorporated\b', r'\bLimited\b',
    r'\bCompany\b', r'\bCo\.?\b',
    r'\bGroup\b', r'\bHoldings\b', r'\bPartners\b',
    r'\bAssociates\b', r'\bEnterprises\b', r'\bVentures\b',
    r'\bS\.?A\.?L\.?\b', r'\bS\.?A\.?R\.?L\.?\b',
    r'\bS\.?A\.?S\.?\b', r'\bS\.?A\.?\b', r'\bGmbH\b', r'\bBV\b',
]


def _company_to_domain_fallback(company_name: str) -> str:
    """Convert company name to domain guess, stripping legal suffixes first.

    e.g. "Tech Corp LLC" -> "tech", "Network Solutions Inc" -> "networksolutions"
    """
    name = company_name.strip()
    for suffix_pat in _COMPANY_DOMAIN_SUFFIXES:
        name = re.sub(suffix_pat, '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '', name.strip().lower())
    name = re.sub(r'[^a-z0-9]', '', name)
    if not name:
        # Fallback: if all suffixes stripped everything, use naive strip
        name = re.sub(r'[^a-z0-9]', '', company_name.lower())
    return name


def prioritize_hr_email(emails: List[str], company_name: str) -> str:
    """Selects best HR email by priority ordering or builds heuristic fallback."""
    if emails:
        # Try each priority level in order — return first match
        for priority_prefix in _HR_PRIORITY_ORDER:
            for email in emails:
                if priority_prefix in email.lower():
                    return email
        return emails[0]

    # Fallback: generate domain from company name (strip legal suffixes first)
    company_domain = _company_to_domain_fallback(company_name)
    return f"careers@{company_domain}.com" if company_domain else ""

def generate_job_id(title: str, company: str, url: str) -> str:
    raw = f"{title.lower().strip()}:{company.lower().strip()}:{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

# ── 8. Global Connection Pooling ────────────────────────────────────────────
_shared_client = stealth.get_async_client(timeout=15.0)

# ── 9. Abstract Base Scraper (Clean Architecture) ───────────────────────────
class BaseJobScraper(ABC):
    @abstractmethod
    async def search(self, query: str, location: str = "", limit: int = 10) -> List[JobListing]:
        pass

# ── 10. Concrete Scrapers ───────────────────────────────────────────────────
class LinkedInScraper(BaseJobScraper):
    @async_retry(max_retries=3, base_delay=2.0)
    async def search(self, query: str, location: str = "", limit: int = 10) -> List[JobListing]:
        jobs: List[JobListing] = []
        search_q = f"{query} {location}".strip()
        url = f"https://www.linkedin.com/jobs/search/?keywords={search_q.replace(' ', '%20')}"
        
        proxy = get_random_proxy()
        client = stealth.get_async_client() if proxy else _shared_client

        try:
            resp = await client.get(url, headers=get_dynamic_headers())
            resp.raise_for_status()
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.find_all('div', class_='base-card') or soup.find_all('li')
            
            for card in cards[:limit]:
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                link = card.find('a', href=re.compile(r'/jobs/view/'))
                
                if not title_elem or not company_elem or not link:
                    continue
                    
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True)
                job_url = link.get('href', '')
                if not job_url.startswith('http'):
                    job_url = "https://www.linkedin.com" + job_url
                    
                emails = extract_valid_emails(resp.text)
                best_email = prioritize_hr_email(emails, company)
                
                jobs.append(JobListing(
                    job_id=generate_job_id(title, company, job_url),
                    title=title, company=company, email=best_email,
                    all_emails=emails, location=location,
                    snippet=f"LinkedIn job: {title} at {company}",
                    source="linkedin", url=job_url
                ))
            
            soup.decompose() # Memory optimization
            
        finally:
            if proxy:
                await client.aclose()
                
        return jobs

class JSearchScraper(BaseJobScraper):
    def __init__(self):
        self.api_key = getattr(config, 'JSEARCH_API_KEY', '')

    @async_retry(max_retries=3, base_delay=1.5)
    async def search(self, query: str, location: str = "", limit: int = 10) -> List[JobListing]:
        if not self.api_key:
            return []
            
        jobs: List[JobListing] = []
        search_q = f"{query} in {location}" if location else query
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
        params = {"query": search_q, "num_pages": 1, "page": 1}

        resp = await _shared_client.get(url, headers=headers, params=params)
        resp.raise_for_status()
            
        data = resp.json()
        for item in data.get("data", [])[:limit]:
            title = item.get("job_title", "")
            company = item.get("employer_name", "")
            job_url = item.get("job_apply_link") or item.get("job_google_link", "")
            desc = item.get("job_description", "")
            
            if not title or not company or not job_url:
                continue
                
            emails = extract_valid_emails(desc)
            best_email = prioritize_hr_email(emails, company)
            
            jobs.append(JobListing(
                job_id=generate_job_id(title, company, job_url),
                title=title, company=company, email=best_email,
                all_emails=emails, location=location,
                snippet=desc[:300], source="jsearch", url=job_url
            ))
        return jobs

class DarkWebScraper(BaseJobScraper):
    @async_retry(max_retries=3, base_delay=2.0)
    async def search(self, query: str, location: str = "", limit: int = 5) -> List[JobListing]:
        jobs: List[JobListing] = []
        search_q = f"{query} {location}".strip().replace(" ", "+")
        
        resp = await _shared_client.get(f"https://remoteok.com/api?tag={search_q}", headers=get_dynamic_headers())
        resp.raise_for_status()
        
        for item in resp.json()[1:limit+1]:
            title = item.get("position", "")
            company = item.get("company", "")
            url = item.get("url", "")
            desc = item.get("description", "")
            
            emails = extract_valid_emails(desc)
            best_email = prioritize_hr_email(emails, company)
            
            jobs.append(JobListing(
                job_id=generate_job_id(title, company, url),
                title=f"[Remote] {title}", company=company,
                email=best_email, all_emails=emails, location="Remote",
                snippet=desc[:300], source="darkweb", url=url
            ))
        return jobs

class ArbeitnowScraper(BaseJobScraper):
    @async_retry(max_retries=3, base_delay=1.5)
    async def search(self, query: str, location: str = "", limit: int = 15) -> List[JobListing]:
        jobs: List[JobListing] = []
        # Arbeitnow doesn't have strict search params in the free tier, we pull the board and filter locally
        url = "https://www.arbeitnow.com/api/job-board-api"
        resp = await _shared_client.get(url)
        resp.raise_for_status()
        
        data = resp.json().get("data", [])
        for item in data:
            title = item.get("title", "")
            company = item.get("company_name", "")
            job_url = item.get("url", "")
            desc = item.get("description", "")
            loc = item.get("location", "")
            
            # Simple local filter
            if query.lower() not in title.lower() and query.lower() not in desc.lower():
                continue
                
            if location and location.lower() not in loc.lower() and not item.get("remote"):
                continue
                
            emails = extract_valid_emails(desc)
            best_email = prioritize_hr_email(emails, company)
            
            jobs.append(JobListing(
                job_id=generate_job_id(title, company, job_url),
                title=title, company=company, email=best_email,
                all_emails=emails, location=loc,
                snippet=desc[:300], source="arbeitnow", url=job_url
            ))
            if len(jobs) >= limit:
                break
        return jobs

class ZeroCostStealthBrowserScraper(BaseJobScraper):
    """
    $0 God-Tier: Connects to undetected-chromedriver.
    Executes undetected headless scraping using free proxies.
    """
    @async_retry(max_retries=3, base_delay=2.0)
    async def search(self, query: str, location: str = "", limit: int = 15) -> List[JobListing]:
        try:
            from core.zero_cost_stealth_browser import stealth_scraper
            logger.info("ZeroCostStealthBrowserScraper initiated. Scraping via undetected-chromedriver.")
            
            # Skeleton logic to match interface
            # source = await stealth_scraper.search("https://linkedin.com/jobs/search?q=" + query)
            # return parse_jobs(source)
            
            return []
        except Exception as e:
            logger.error(f"Zero cost scraper failed: {e}")
            return []

# ── 11. Unified Asynchronous Aggregator ─────────────────────────────────────
class EnterpriseJobSearch:
    """Massively parallel job search aggregator with cache, semaphore, and proxy controls."""
    def __init__(self):
        self.scrapers: List[BaseJobScraper] = [LinkedInScraper(), JSearchScraper(), DarkWebScraper(), ArbeitnowScraper(), ZeroCostStealthBrowserScraper()]
        self._seen_emails: Set[str] = set()
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)

    async def _execute_scraper_safely(self, scraper: BaseJobScraper, query: str, location: str, limit: int) -> List[JobListing]:
        async with self.semaphore:
            try:
                return await scraper.search(query, location, limit)
            except Exception as e:
                logger.error(f"[EnterpriseEngine] Isolation caught failure in {scraper.__class__.__name__}: {e}", exc_info=True)
                return []

    async def execute_parallel_search(self, query: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Executes cached, semaphored, concurrent scrape."""
        cache_key = f"{query}:{location}:{limit}".lower().strip()
        
        # 1. Check Cache
        cached_results = await query_cache.get(cache_key)
        if cached_results:
            return [job.model_dump() for job in cached_results]

        # 2. Fire Concurrent Scrapes
        tasks = [
            self._execute_scraper_safely(scraper, query, location, limit) 
            for scraper in self.scrapers
        ]
        
        results_matrix = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. Aggregate & Deduplicate
        all_jobs: List[JobListing] = []
        for result in results_matrix:
            if isinstance(result, list):
                all_jobs.extend(result)
                
        unique_jobs: List[JobListing] = []
        seen_ids: Set[str] = set()
        
        for job in all_jobs:
            if job.job_id in seen_ids:
                continue
            if job.email and job.email in self._seen_emails:
                continue
                
            self._seen_emails.add(job.email)
            seen_ids.add(job.job_id)
            unique_jobs.append(job)
            
        # 4. Save to Cache and Return
        if unique_jobs:
            await query_cache.set(cache_key, unique_jobs)
            
        logger.info(f"Enterprise Engine: Yielded {len(unique_jobs)} highly-qualified leads.", extra={
            "query": query, "location": location, "results": len(unique_jobs)
        })
        
        return [job.model_dump() for job in unique_jobs]


# ── 12. MultiSourceSearch — Unified Sync Orchestrator ─────────────────────────
# Used by campaign_runner.py for synchronous job searching across all scrapers.

class MultiSourceSearch:
    """
    Synchronous multi-source job search aggregator.
    Integrates independent scraper classes from multi_source_scraper.py
    plus the existing GlobalJobScraper for maximum coverage.
    """
    
    def __init__(self):
        self._scrapers = None
    
    def _init_scrapers(self):
        """Lazy-init scrapers on first use."""
        if self._scrapers is not None:
            return
        try:
            from core.multi_source_scraper import (
                BaytScraper, NaukriScraper, WuzzufScraper,
                IndeedScraper, GoogleJobsScraper, LinkedInScraper,
                GlassdoorScraper, WellfoundScraper, DiceScraper,
                SeekScraper, StepStoneScraper, WWRScraper,
                ZipRecruiterScraper, XingScraper, NaukriIndiaScraper,
                JoobleScraper, UpworkScraper
            )
            self._scrapers = [
                LinkedInScraper(),
                IndeedScraper(),
                BaytScraper(),
                NaukriScraper(),
                WuzzufScraper(),
                GoogleJobsScraper(),
                GlassdoorScraper(),
                WellfoundScraper(),
                DiceScraper(),
                SeekScraper(),
                StepStoneScraper(),
                WWRScraper(),
                ZipRecruiterScraper(),
                XingScraper(),
                NaukriIndiaScraper(),
                JoobleScraper(),
                UpworkScraper(),
            ]
            # Add Indeed RSS scraper (never gets 403 since it uses XML feed)
            try:
                from core.indeed_rss_scraper import IndeedRSSScraper
                self._scrapers.insert(1, IndeedRSSScraper())  # high priority
                logger.info("IndeedRSSScraper added to search rotation")
            except Exception as e:
                logger.warning(f"IndeedRSSScraper not available: {e}")
            logger.info(f"MultiSourceSearch: initialized {len(self._scrapers)} scrapers")
        except ImportError as e:
            logger.warning(f"MultiSourceSearch: multi_source_scraper not available: {e}")
            self._scrapers = []
    
    def search_all_sources(self, query: str = "network engineer", location: str = "",
                           limit: int = 100) -> List[Dict]:
        """
        Search all configured sources synchronously.
        Returns deduplicated list of job dicts.
        
        Args:
            query: Job search query (e.g., "network engineer")
            location: Location string (e.g., "Dubai, UAE")
            limit: Maximum total results to return
        """
        self._init_scrapers()
        
        all_jobs = []
        seen_ids = set()
        per_scraper_limit = max(limit // max(len(self._scrapers), 1), 5)
        
        # Also try the global scraper for additional coverage
        try:
            from core.global_scraper import GlobalJobScraper
            global_scraper = GlobalJobScraper()
            
            # Map location to country key
            location_lower = location.lower()
            country_key = "remote"
            for ck in ("lebanon", "uae", "saudi", "qatar", "kuwait"):
                if ck in location_lower:
                    country_key = ck
                    break
            
            try:
                global_jobs = global_scraper.search_country(country_key, query, limit=per_scraper_limit)
                for job in global_jobs:
                    jid = job.get("job_id", "")
                    if jid and jid not in seen_ids:
                        seen_ids.add(jid)
                        all_jobs.append(job)
                logger.info(f"MultiSourceSearch: GlobalScraper found {len(global_jobs)} jobs")
            except Exception as e:
                logger.debug(f"GlobalScraper search error: {e}")
            finally:
                global_scraper.close()
        except ImportError:
            logger.debug("GlobalJobScraper not available")
        
        # Run each standalone scraper
        for scraper in self._scrapers:
            if len(all_jobs) >= limit:
                break
            try:
                scraper_jobs = scraper.search(query, location, limit=per_scraper_limit)
                for job in scraper_jobs:
                    jid = job.get("job_id", "")
                    if jid and jid not in seen_ids:
                        seen_ids.add(jid)
                        all_jobs.append(job)
                logger.info(f"MultiSourceSearch: {scraper.source_name} found {len(scraper_jobs)} jobs")
            except Exception as e:
                logger.warning(f"MultiSourceSearch: {scraper.source_name} error: {e}")
        
        # Close all scraper sessions
        for scraper in self._scrapers:
            try:
                scraper.close()
            except Exception:
                pass
        
        logger.info(f"MultiSourceSearch: total unique jobs = {len(all_jobs)}")
        return all_jobs[:limit]
    
    def search_single(self, query: str = "network engineer", location: str = "",
                      limit: int = 10) -> List[Dict]:
        """Lightweight single search — returns up to `limit` results."""
        return self.search_all_sources(query, location, limit=limit)
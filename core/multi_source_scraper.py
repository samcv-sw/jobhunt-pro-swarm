"""
Multi-Source Job Scraper — Independent scraper classes for each platform.
Integrates with MultiSourceSearch orchestrator in job_search.py.

Scrapers: Bayt, NaukriGulf, Wuzzuf, Indeed, Google Jobs, LinkedIn, Glassdoor
Each scraper is a standalone class following BaseScraper interface.
"""
import re
import random
import time
import logging
import hashlib
from typing import List, Dict, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
BLOCKED_EMAILS = [
    'noreply@', 'no-reply@', 'donotreply@', 'example.com', 'test.com',
    'w3.org', 'schema.org', 'sentry', 'webpack', 'facebook.com',
    'google.com', 'github.com', 'microsoft.com', 'apple.com',
    'cloudflare.com', 'jquery.com', 'wikipedia.org', 'youtube.com',
    'twitter.com', 'instagram.com', 'linkedin.com', 'tiktok.com',
    'sentry.io', 'noreply.', 'no-reply.', 'donotreply.',
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
]

# ── Helpers ─────────────────────────────────────────────────────
def _make_job_id(title: str, company: str, url: str = "") -> str:
    raw = f"{title.lower().strip()}:{company.lower().strip()}:{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def _get_headers(extra: Dict = None) -> Dict[str, str]:
    h = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    if extra:
        h.update(extra)
    return h

def _extract_emails(text: str) -> List[str]:
    if not text:
        return []
    emails = EMAIL_PATTERN.findall(text)
    return [
        e.lower().strip()
        for e in emails
        if not any(b in e.lower() for b in BLOCKED_EMAILS)
        and len(e) < 100
        and '.' in e.split('@')[1]
        and not e.endswith(('.png', '.jpg', '.gif', '.svg'))
    ]

def _placeholder_email(company: str, prefix: str = "careers") -> str:
    domain = re.sub(r'[^a-z0-9]', '', company.lower())
    return f"{prefix}@{domain}.com" if domain else ""

def _extract_salary(text: str) -> Optional[float]:
    if not text:
        return None
    patterns = [
        re.compile(r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|K)?', re.IGNORECASE),
        re.compile(r'([\d,]+(?:\.\d{2})?)\s*(?:USD|usd|\$)', re.IGNORECASE),
        re.compile(r'(?:salary|pay|compensation)[:\s]*\$?\s*([\d,]+)', re.IGNORECASE),
        re.compile(r'(?:AED|د\.إ)\s*([\d,]+)', re.IGNORECASE),
        re.compile(r'(?:SAR|﷼)\s*([\d,]+)', re.IGNORECASE),
        re.compile(r'(?:QAR|ر\.ق)\s*([\d,]+)', re.IGNORECASE),
    ]
    for pat in patterns:
        matches = pat.findall(text)
        for m in matches:
            try:
                return float(re.sub(r'[,$\s]', '', m))
            except ValueError:
                continue
    return None

# ══════════════════════════════════════════════════════════════════
# BASE SCRAPER
# ══════════════════════════════════════════════════════════════════

class BaseScraper:
    """Abstract base class for all job scrapers."""
    
    source_name: str = "base"
    
    def __init__(self, timeout: int = 20, rate_delay: float = 3.0):
        self.timeout = timeout
        self.rate_delay = rate_delay
        self._last_request = 0.0
        self._session = httpx.Client(timeout=timeout, follow_redirects=True)
    
    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self.rate_delay:
            time.sleep(self.rate_delay - elapsed)
        self._last_request = time.time()
    
    def _get(self, url: str, extra_headers: Dict = None, max_retries: int = 2) -> Optional[httpx.Response]:
        for attempt in range(max_retries + 1):
            try:
                self._rate_limit()
                headers = _get_headers(extra_headers)
                resp = self._session.get(url, headers=headers)
                if resp.status_code in (429, 503):
                    delay = min(30, (attempt + 1) * 5)
                    logger.debug(f"{self.source_name}: rate limited, waiting {delay}s")
                    time.sleep(delay)
                    continue
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 403:
                    logger.debug(f"{self.source_name}: 403 forbidden")
                    return resp
            except Exception as e:
                logger.debug(f"{self.source_name}: request error: {e}")
                if attempt < max_retries:
                    time.sleep(2)
        return None
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Search for jobs. Override in subclasses."""
        raise NotImplementedError
    
    def close(self):
        try:
            self._session.close()
        except Exception:
            pass
    
    def _build_job_dict(self, title: str, company: str, location: str, 
                         url: str = "", snippet: str = "", emails: List[str] = None,
                         salary: Optional[float] = None) -> Dict:
        emails = emails or []
        placeholders = [f"careers@{re.sub(r'[^a-z0-9]', '', company.lower())}.com"] if company else []
        all_emails = emails if emails else placeholders
        return {
            "job_id": _make_job_id(title, company, url),
            "title": title,
            "company": company,
            "email": all_emails[0] if all_emails else "",
            "all_emails": all_emails,
            "location": location,
            "snippet": snippet or f"{self.source_name}: {title} at {company}",
            "source": self.source_name,
            "url": url,
            "salary": salary,
        }


# ══════════════════════════════════════════════════════════════════
# BAYT.COM SCRAPER
# ══════════════════════════════════════════════════════════════════

class BaytScraper(BaseScraper):
    """Scraper for Bayt.com — #1 job site in the Middle East."""
    source_name = "bayt"
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        location_parts = location.split(",") if location else [""]
        
        for loc in location_parts[:3]:
            loc = loc.strip()
            try:
                q = quote_plus(query)
                loc_q = quote_plus(loc) if loc else ""
                if loc_q:
                    url = f"https://www.bayt.com/en/international/jobs/?q={q}&location={loc_q}"
                else:
                    url = f"https://www.bayt.com/en/international/jobs/?q={q}"
                
                resp = self._get(url, extra_headers={'Referer': 'https://www.bayt.com/en/international/'})
                if not resp or resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = (
                    soup.find_all('li', class_='has-pointer-d') or
                    soup.select('div.job-card') or
                    soup.select('article.is-available') or
                    soup.find_all('div', class_='card')
                )
                
                for card in cards[:limit]:
                    job = self._parse_card(card, location)
                    if job:
                        jobs.append(job)
                        if len(jobs) >= limit:
                            break
            except Exception as e:
                logger.debug(f"BaytScraper: error for '{loc}': {e}")
                continue
            
            if len(jobs) >= limit:
                break
        
        return jobs
    
    def _parse_card(self, card, fallback_location: str) -> Optional[Dict]:
        title_elem = (
            card.find('h2', class_='jb-title') or card.find('h2') or
            card.find('a', class_='job-title') or
            card.find('a', href=re.compile(r'/en/international/jobs/', re.I))
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        company_elem = (
            card.find('span', class_='jb-company') or card.find('span', class_='company') or
            card.find('b', class_='company-name') or
            card.find('a', href=re.compile(r'/en/company/', re.I))
        )
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        if not title or not company:
            return None
        
        location_elem = (
            card.find('span', class_='jb-location') or card.find('span', class_='location')
        )
        loc = location_elem.get_text(strip=True) if location_elem else fallback_location
        
        link = card.find('a', href=re.compile(r'/en/international/jobs/', re.I))
        job_url = ""
        if link:
            href = link.get('href', '')
            job_url = f"https://www.bayt.com{href}" if href.startswith('/') else href
        
        desc_elem = card.find('p', class_='jb-desc') or card.find('div', class_='job-description')
        snippet = desc_elem.get_text(strip=True)[:300] if desc_elem else ""
        
        return self._build_job_dict(title, company, loc, job_url, snippet)


# ══════════════════════════════════════════════════════════════════
# NAUKRIGULF SCRAPER
# ══════════════════════════════════════════════════════════════════

class NaukriScraper(BaseScraper):
    """Scraper for NaukriGulf.com — Gulf region jobs."""
    source_name = "naukrigulf"
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        location_parts = location.split(",") if location else [""]
        
        for loc in location_parts[:3]:
            loc = loc.strip()
            try:
                q = quote_plus(query)
                loc_slug = quote_plus(loc.replace(" ", "-")) if loc else ""
                
                if loc_slug:
                    url = f"https://www.naukrigulf.com/{q}-jobs-in-{loc_slug}"
                else:
                    url = f"https://www.naukrigulf.com/jobs?q={q}"
                
                resp = self._get(url, extra_headers={'Referer': 'https://www.naukrigulf.com/'})
                if not resp or resp.status_code != 200:
                    # Try alternative URL format
                    if loc:
                        url = f"https://www.naukrigulf.com/jobs?q={q}&l={quote_plus(loc)}"
                        resp = self._get(url)
                        if not resp or resp.status_code != 200:
                            continue
                    else:
                        continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = (
                    soup.find_all('article', class_='jobTuple') or
                    soup.select('div.row.job') or
                    soup.find_all('div', class_='job-card') or
                    soup.select('li.desktop-search-result')
                )
                
                for card in cards[:limit]:
                    job = self._parse_card(card, location)
                    if job:
                        jobs.append(job)
                        if len(jobs) >= limit:
                            break
            except Exception as e:
                logger.debug(f"NaukriScraper: error for '{loc}': {e}")
                continue
            
            if len(jobs) >= limit:
                break
        
        return jobs
    
    def _parse_card(self, card, fallback_location: str) -> Optional[Dict]:
        title_elem = (
            card.find('a', class_='title') or card.find('h2', class_='job-title') or
            card.find('a', href=re.compile(r'/job-', re.I)) or
            card.find('a', class_='job-card-title')
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        title = re.sub(r'\s+', ' ', title).strip()
        
        company_elem = (
            card.find('span', class_='company-name') or card.find('a', class_='company') or
            card.find('span', class_='subTitle') or card.find('span', class_='company')
        )
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        if not title or not company:
            return None
        
        location_elem = (
            card.find('span', class_='location') or card.find('span', class_='loc') or
            card.find('li', class_='location')
        )
        loc = location_elem.get_text(strip=True) if location_elem else fallback_location
        
        link = card.find('a', href=re.compile(r'/job-', re.I))
        job_url = ""
        if link:
            href = link.get('href', '')
            job_url = f"https://www.naukrigulf.com{href}" if href.startswith('/') else href
        
        salary_elem = card.find('span', class_='salary')
        salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
        salary = _extract_salary(salary_text) if salary_text else None
        
        return self._build_job_dict(title, company, loc, job_url, 
                                     salary=salary)


# ══════════════════════════════════════════════════════════════════
# WUZZUF SCRAPER
# ══════════════════════════════════════════════════════════════════

class WuzzufScraper(BaseScraper):
    """Scraper for Wuzzuf.net — Egypt & MENA jobs."""
    source_name = "wuzzuf"
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        try:
            q = quote_plus(query)
            url = f"https://wuzzuf.net/search/jobs/?q={q}"
            
            if location:
                url += f"&location={quote_plus(location)}"
            
            resp = self._get(url, extra_headers={'Referer': 'https://wuzzuf.net/'})
            if not resp or resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = (
                soup.find_all('div', class_='css-1gq4cwl') or
                soup.select('div.job-card') or
                soup.find_all('div', class_='card') or
                soup.select('a.css-1w3khdb') or
                soup.find_all('div', class_='job')
            )
            
            for card in cards[:limit]:
                job = self._parse_card(card, location)
                if job:
                    jobs.append(job)
        except Exception as e:
            logger.debug(f"WuzzufScraper: error: {e}")
        
        return jobs
    
    def _parse_card(self, card, fallback_location: str) -> Optional[Dict]:
        title_elem = (
            card.find('h2', class_='css-m604qf') or card.find('h2') or
            card.find('a', href=re.compile(r'/jobs/', re.I)) or
            card.find('a', class_='job-title')
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        title = re.sub(r'\s+', ' ', title).strip()
        
        company_elem = (
            card.find('a', class_='css-17s97q8') or card.find('span', class_='company') or
            card.find('div', class_='company')
        )
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        if not title or not company:
            return None
        
        location_elem = (
            card.find('span', class_='css-5wys0k') or card.find('span', class_='location') or
            card.find('div', class_='location')
        )
        loc = location_elem.get_text(strip=True) if location_elem else fallback_location
        
        link = card.find('a', href=re.compile(r'/jobs/', re.I))
        job_url = ""
        if link:
            href = link.get('href', '')
            job_url = f"https://wuzzuf.net{href}" if href.startswith('/') else href
        
        return self._build_job_dict(title, company, loc, job_url)


# ══════════════════════════════════════════════════════════════════
# INDEED SCRAPER
# ══════════════════════════════════════════════════════════════════

class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com — world's largest job board."""
    source_name = "indeed"
    
    # Domain mapping for regional Indeed sites
    DOMAINS = {
        "lebanon": "www.indeed.com.lb",
        "uae": "www.indeed.ae",
        "saudi": "www.indeed.com.sa",
        "qatar": "www.indeed.qa",
        "kuwait": "www.indeed.com.kw",
        "remote": "www.indeed.com",
        "default": "www.indeed.com",
    }
    
    def __init__(self, country: str = "default", **kwargs):
        super().__init__(**kwargs)
        self.domain = self.DOMAINS.get(country.lower(), self.DOMAINS["default"])
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        location_parts = location.split(",") if location else [""]
        
        for loc in location_parts[:3]:
            loc = loc.strip()
            try:
                q = quote_plus(query)
                loc_q = quote_plus(loc) if loc else ""
                url = f"https://{self.domain}/jobs?q={q}&l={loc_q}"
                
                resp = self._get(url)
                if not resp or resp.status_code not in (200, 301, 302):
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = (
                    soup.find_all('div', class_='job_seen_beacon') or
                    soup.find_all('div', class_='jobsearch-SerpJobCard') or
                    soup.find_all('div', class_='result') or
                    soup.select('div.job-card-container') or
                    soup.select('li.css-5lf6m') or
                    soup.select('div.cardOutline') or
                    soup.select('td.resultContent')
                )
                
                for card in cards[:limit]:
                    job = self._parse_card(card, location, loc)
                    if job:
                        jobs.append(job)
                        if len(jobs) >= limit:
                            break
            except Exception as e:
                logger.debug(f"IndeedScraper: error for '{loc}': {e}")
                continue
            
            if len(jobs) >= limit:
                break
        
        return jobs
    
    def _parse_card(self, card, fallback_location: str, city: str) -> Optional[Dict]:
        # Title
        title_elem = (
            card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle') or
            card.find('h2', class_='title') or card.find('a', {'data-jk': True}) or
            card.find('a', id=re.compile(r'job_')) or
            card.find('span', title=True)
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Company
        company_elem = (
            card.find('span', class_='companyName') or card.find('span', class_='company') or
            card.find('div', class_='company_location') or
            card.find('span', {'data-testid': 'company-name'}) or
            card.find('a', class_='companyOverviewLink')
        )
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        # Location
        location_elem = (
            card.find('div', class_='companyLocation') or card.find('span', class_='location') or
            card.find('span', {'data-testid': 'text-location'})
        )
        location = location_elem.get_text(strip=True) if location_elem else city or fallback_location
        
        if not title or not company:
            return None
        
        # URL
        link = card.find('a', href=re.compile(r'/jobs|/pagead|/rc/clk|/viewjob', re.I))
        job_url = ""
        if link:
            href = link.get('href', '')
            if href.startswith('/'):
                job_url = f"https://{self.domain}{href}"
            elif href.startswith('http'):
                job_url = href
        
        # Salary
        salary_elem = (
            card.find('div', class_='salary-snippet') or card.find('span', class_='salaryText') or
            card.find('span', {'data-testid': 'salary-info'})
        )
        salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
        salary = _extract_salary(salary_text) if salary_text else None
        
        # Snippet
        snippet_elem = (
            card.find('div', class_='job-snippet') or card.find('div', class_='summary') or
            card.find('ul', class_='job-snippet-list')
        )
        snippet = snippet_elem.get_text(strip=True)[:300] if snippet_elem else ""
        
        return self._build_job_dict(title, company, location, job_url, snippet, salary=salary)


# ══════════════════════════════════════════════════════════════════
# GOOGLE JOBS SCRAPER
# ══════════════════════════════════════════════════════════════════

class GoogleJobsScraper(BaseScraper):
    """Scraper for Google Jobs — aggregates across all job boards."""
    source_name = "google_jobs"
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        try:
            # Build a search query targeting job boards
            site_filters = [
                "site:linkedin.com/jobs",
                "site:indeed.com",
                "site:bayt.com",
                "site:naukrigulf.com",
                "site:gulftalent.com",
                "site:glassdoor.com",
            ]
            site_filter = " OR ".join(site_filters)
            loc_str = f" in {location}" if location else ""
            search_q = f"{query}{loc_str} {site_filter}"
            
            url = f"https://www.google.com/search?q={quote_plus(search_q)}&num=20&hl=en"
            
            resp = self._get(url, extra_headers={'Referer': 'https://www.google.com/'})
            if not resp or resp.status_code != 200:
                return jobs
            
            # Extract URLs from Google search results
            all_urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
            job_board_domains = [
                'linkedin.com/jobs', 'indeed.com', 'bayt.com', 'naukrigulf.com',
                'gulftalent.com', 'wuzzuf.net', 'glassdoor.com', 'monster.com',
                'remoteok.com', 'weworkremotely.com', 'jobspresso.com', 'ziprecruiter.com',
            ]
            job_urls = []
            seen = set()
            for u in all_urls:
                if any(d in u.lower() for d in job_board_domains):
                    if u not in seen:
                        seen.add(u)
                        job_urls.append(u)
                        if len(job_urls) >= limit * 2:
                            break
            
            logger.debug(f"GoogleJobsScraper: found {len(job_urls)} job URLs")
            
            # Also parse organic results for faster extraction
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Try to find Google Jobs special widget
            for result in soup.select('div.g')[:limit * 2]:
                try:
                    link_elem = result.find('a', href=True)
                    if not link_elem:
                        continue
                    href = link_elem.get('href', '')
                    if not any(d in href.lower() for d in job_board_domains):
                        continue
                    
                    title_elem = result.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else query
                    
                    snippet_elem = result.find('div', class_='VwiC3b') or result.find('span', class_='aCOpRe')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Try to extract company from snippet
                    company = "Unknown"
                    company_elem = result.find('span', class_='VuuXrf')
                    if company_elem:
                        company = company_elem.get_text(strip=True)
                    
                    loc_text = f"{location}" if location else "Remote"
                    
                    job = self._build_job_dict(title, company, loc_text, href, snippet[:200])
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break
                except Exception:
                    continue
            
            # If we didn't get enough from organic, fetch individual pages
            if len(jobs) < limit:
                for job_url in job_urls:
                    if len(jobs) >= limit:
                        break
                    try:
                        page_job = self._fetch_page(job_url, location)
                        if page_job:
                            jobs.append(page_job)
                    except Exception:
                        continue
            
        except Exception as e:
            logger.debug(f"GoogleJobsScraper: error: {e}")
        
        return jobs
    
    def _fetch_page(self, url: str, location: str) -> Optional[Dict]:
        try:
            resp = self._get(url)
            if not resp or resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text(strip=True)[:200] if title_elem else "Position"
            title = re.sub(r'\s+', ' ', title).strip()
            
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            company = domain.split('.')[0].title()
            
            emails = _extract_emails(resp.text)
            
            return self._build_job_dict(title, company, location or "Remote", url,
                                         f"Google Jobs: {title} at {company}",
                                         emails=emails,
                                         salary=_extract_salary(resp.text))
        except Exception as e:
            logger.debug(f"GoogleJobsScraper: page fetch error: {e}")
            return None


# ══════════════════════════════════════════════════════════════════
# LINKEDIN SCRAPER (standalone class)
# ══════════════════════════════════════════════════════════════════

class LinkedInScraper(BaseScraper):
    """Standalone LinkedIn scraper class."""
    source_name = "linkedin"
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        location_parts = location.split(",") if location else [""]
        
        for loc in location_parts[:3]:
            loc = loc.strip()
            try:
                search_q = f"{query} {loc}".strip()
                url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(search_q)}&location={quote_plus(loc)}"
                
                resp = self._get(url)
                if not resp:
                    continue
                if resp.status_code == 403:
                    logger.debug("LinkedInScraper: blocked (403)")
                    continue
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = (
                    soup.find_all('div', class_='base-card') or
                    soup.find_all('li', class_='jobs-search-results__list-item') or
                    soup.select('div.job-search-card') or
                    soup.select('div.base-search-card')
                )
                
                for card in cards[:limit]:
                    job = self._parse_card(card, location)
                    if job:
                        jobs.append(job)
                        if len(jobs) >= limit:
                            break
            except Exception as e:
                logger.debug(f"LinkedInScraper: error for '{loc}': {e}")
                continue
            
            # Random delay between cities to avoid LinkedIn blocks
            time.sleep(random.uniform(3, 6))
        
        return jobs
    
    def _parse_card(self, card, fallback_location: str) -> Optional[Dict]:
        title_elem = (
            card.find('h3', class_='base-search-card__title') or card.find('h3') or
            card.find('span', class_='sr-only')
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        company_elem = (
            card.find('h4', class_='base-search-card__subtitle') or card.find('h4')
        )
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        if not title or not company:
            return None
        
        link = card.find('a', href=re.compile(r'/jobs/view/', re.I))
        if not link:
            link = card.find('a', class_='base-card__full-link')
        
        job_url = ""
        if link:
            href = link.get('href', '')
            job_url = href if href.startswith('http') else f"https://www.linkedin.com{href}"
        
        location_elem = (
            card.find('span', class_='job-search-card__location') or
            card.find('span', class_='job-card-container__metadata-item')
        )
        loc = location_elem.get_text(strip=True) if location_elem else fallback_location
        
        return self._build_job_dict(title, company, loc, job_url,
                                     f"LinkedIn: {title} at {company}")


# ══════════════════════════════════════════════════════════════════
# GLASSDOOR SCRAPER
# ══════════════════════════════════════════════════════════════════

class GlassdoorScraper(BaseScraper):
    """Standalone Glassdoor scraper — best effort (aggressive anti-bot)."""
    source_name = "glassdoor"
    
    def search(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        jobs = []
        try:
            q = quote_plus(query)
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}&locT=C&locId=0"
            
            if location:
                url += f"&locKeyword={quote_plus(location)}"
            
            resp = self._get(url, extra_headers={'Referer': 'https://www.glassdoor.com/'})
            if not resp:
                return jobs
            if resp.status_code == 403:
                logger.debug("GlassdoorScraper: blocked (403)")
                return jobs
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = (
                soup.find_all('li', class_='react-job-listing') or
                soup.select('div.jobListing') or
                soup.find_all('div', class_='jobTitle') or
                soup.find_all('a', class_='job-title')
            )
            
            for card in cards[:limit]:
                job = self._parse_card(card, location)
                if job:
                    jobs.append(job)
        except Exception as e:
            logger.debug(f"GlassdoorScraper: error: {e}")
        
        return jobs
    
    def _parse_card(self, card, fallback_location: str) -> Optional[Dict]:
        title_elem = (
            card.find('a', class_='job-title') or card.find('h2') or
            card.find('a', {'data-test': 'job-link'})
        )
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        company_elem = (
            card.find('span', class_='job-employer') or card.find('span', class_='company-name') or
            card.find('div', {'data-test': 'employer-name'})
        )
        company = company_elem.get_text(strip=True) if company_elem else ""
        
        if not title or not company:
            return None
        
        location_elem = (
            card.find('span', class_='job-location') or card.find('span', class_='location') or
            card.find('div', {'data-test': 'location'})
        )
        loc = location_elem.get_text(strip=True) if location_elem else fallback_location
        
        return self._build_job_dict(title, company, loc)

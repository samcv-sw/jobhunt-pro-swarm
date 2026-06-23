"""
PAJobScraper v2 — Optimized for PA Free Tier
- JSearch API with smart caching (2h TTL) to conserve 300/month quota
- LinkedIn XHR as fallback
- Reduces API calls from 15/tick to ~3/tick (with cache)
"""

import logging
import os
import time
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# JSearch API config
JSEARCH_KEY = os.getenv("JSEARCH_API_KEY", "4661cb4462msh784e5b26afc61cfp158ffbjsn19689ea28233")
JSEARCH_BACKUP = os.getenv("JSEARCH_BACKUP_KEY", "7085d5ad11msh996c8add34ca2a5p106c72jsn7beaa25f86e2")

COUNTRIES = {
    "lebanon": "lb",
    "uae": "ae",
    "saudi": "sa",
    "qatar": "qa",
    "kuwait": "kw",
    "remote": "",
}

CITIES = {
    "lebanon": "Beirut",
    "uae": "Dubai",
    "saudi": "Riyadh",
    "qatar": "Doha",
    "kuwait": "Kuwait City",
}

TITLES = [
    "network engineer",
    "network administrator",
    "it support engineer",
    "system administrator",
    "network architect",
    "network security",
    "infrastructure engineer",
    "telecom engineer",
    "it manager",
]

# ── Smart Cache ──────────────────────────────────────────────────────────
_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '_scraper_cache.json')
_CACHE_TTL = 7200  # 2 hours


def _load_cache():
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, 'r') as f:
                data = json.load(f)
            return data.get("ts", 0), data.get("jobs", [])
    except Exception:
        pass
    return 0, []


def _save_cache(jobs):
    try:
        dirname = os.path.dirname(_CACHE_FILE)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        with open(_CACHE_FILE, 'w') as f:
            json.dump({"ts": time.time(), "jobs": jobs}, f)
    except Exception:
        pass


class PAJobScraper:
    def __init__(self):
        self.jsearch_keys = [JSEARCH_KEY, JSEARCH_BACKUP]
        self._key_idx = 0

    def _jsearch_request(self, query: str, country_code: str = "", page: int = 1) -> List[Dict]:
        """Make JSearch API request with key rotation."""
        for attempt in range(len(self.jsearch_keys)):
            key = self.jsearch_keys[self._key_idx % len(self.jsearch_keys)]
            self._key_idx += 1
            try:
                url = f"https://jsearch.p.rapidapi.com/search?query={urllib.request.quote(query)}&page={page}&num_pages=1"
                if country_code:
                    url += f"&country={country_code}"
                req = urllib.request.Request(url, headers={
                    "X-RapidAPI-Key": key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                    "User-Agent": "Mozilla/5.0"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                jobs = []
                for j in data.get("data", []):
                    employer = j.get("employer_name", "") or ""
                    title = j.get("job_title", "") or ""
                    city = j.get("job_city", "") or ""
                    country = j.get("job_country", "") or ""
                    apply_link = j.get("job_apply_link", "") or ""
                    description = j.get("job_description", "") or ""
                    employer_website = j.get("employer_website", "") or ""
                    email = ""
                    if employer_website:
                        email = f"hr@{employer_website.replace('https://','').replace('http://','').split('/')[0]}"
                    elif apply_link:
                        from urllib.parse import urlparse
                        domain = urlparse(apply_link).netloc
                        email = f"careers@{domain}"
                    if employer and title:
                        jobs.append({
                            "id": f"jsearch_{j.get('job_id', str(time.time()))}",
                            "title": title[:100],
                            "company": employer[:80],
                            "location": f"{city}, {country}"[:60] if city else country[:60],
                            "source": "jsearch",
                            "url": apply_link,
                            "email": email,
                            "snippet": description[:200],
                            "job_id": j.get("job_id", ""),
                        })
                return jobs
            except Exception as e:
                logger.warning(f"JSearch attempt {attempt+1} failed: {e}")
                continue
        return []

    def search_jsearch(self, targets: Dict[str, List[str]] = None, max_total: int = 100) -> List[Dict]:
        """Search JSearch API — OPTIMIZED: only 3 queries per call (not 15)."""
        if targets is None:
            # Reduced from 15 queries to 3 to conserve JSearch API quota (300/month)
            # Rotate titles each call to eventually cover all titles
            import random
            all_country_title_pairs = [
                ("uae", "network engineer"),
                ("uae", "network administrator"),
                ("uae", "it support engineer"),
                ("saudi", "network engineer"),
                ("saudi", "system administrator"),
                ("qatar", "network engineer"),
                ("kuwait", "network engineer"),
                ("lebanon", "network engineer"),
                ("remote", "network engineer"),
                ("remote", "network administrator"),
            ]
            # Pick 3 random pairs each time → covers all over ~10 ticks (50 min)
            selected = random.sample(all_country_title_pairs, min(3, len(all_country_title_pairs)))
            targets = {}
            for ck, title in selected:
                targets.setdefault(ck, []).append(title)

        all_jobs = []
        seen = set()
        seen_urls = set()

        for country_key, titles in targets.items():
            if len(all_jobs) >= max_total:
                break
            country_code = COUNTRIES.get(country_key, "")
            for title in titles:
                if len(all_jobs) >= max_total:
                    break
                try:
                    jobs = self._jsearch_request(title, country_code)
                    for j in jobs:
                        key = (j["company"].lower(), j["title"].lower())
                        u = j.get("url", "")
                        if key not in seen and u not in seen_urls:
                            seen.add(key)
                            if u:
                                seen_urls.add(u)
                            all_jobs.append(j)
                    logger.info(f"JSearch [{country_key}/{title}]: {len(jobs)} jobs")
                    time.sleep(0.3)  # Rate limit
                except Exception as e:
                    logger.warning(f"JSearch [{country_key}/{title}] error: {e}")

        logger.info(f"JSearch total: {len(all_jobs)} unique jobs (3 queries)")
        return all_jobs[:max_total]

    def search_linkedin_xhr(self, max_jobs: int = 50) -> List[Dict]:
        """Search LinkedIn XHR API (works on PA, no auth needed)."""
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("httpx or BeautifulSoup not available")
            return []

        all_jobs = []
        seen = set()
        cities_to_use = list(CITIES.items())
        titles_to_use = TITLES[:3]

        for title in titles_to_use:
            if len(all_jobs) >= max_jobs:
                break
            for country_key, city in cities_to_use:
                if len(all_jobs) >= max_jobs:
                    break
                try:
                    url = (
                        f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                        f"?keywords={urllib.request.quote(title)}"
                        f"&location={urllib.request.quote(city)}&start=0&count=10"
                    )
                    with httpx.Client(timeout=15) as client:
                        resp = client.get(url, headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        })
                        if resp.status_code != 200:
                            continue
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select("li")
                    for card in cards:
                        t_el = card.select_one(".base-search-card__title")
                        c_el = card.select_one(".base-search-card__subtitle")
                        l_el = card.select_one(".job-search-card__location")
                        a_el = card.select_one("a[href*=jobs]")
                        t = t_el.get_text(strip=True) if t_el else ""
                        comp = c_el.get_text(strip=True) if c_el else ""
                        loc = l_el.get_text(strip=True) if l_el else city
                        href = (a_el.get("href", "") if a_el else "").strip()
                        key = (comp.lower().strip(), t.lower().strip())
                        if t and comp and key not in seen:
                            seen.add(key)
                            all_jobs.append({
                                "id": f"li_{len(all_jobs)}",
                                "title": t[:100],
                                "company": comp[:80],
                                "location": str(loc or city)[:60],
                                "source": "linkedin_xhr",
                                "url": href,
                                "email": f"hr@{comp.lower().replace(' ','')}.com",
                                "snippet": "",
                            })
                except Exception as e:
                    logger.debug(f"LinkedIn XHR [{title}/{city}] error: {e}")

        logger.info(f"LinkedIn XHR total: {len(all_jobs)} jobs")
        return all_jobs[:max_jobs]

    def search_all(self, max_jobs: int = 100) -> List[Dict]:
        """
        Primary: Check cache (2h TTL) → JSearch API (3 queries only) → LinkedIn XHR
        Cache saves 12+ JSearch API calls per tick = 300/month quota lasts 100 ticks.
        """
        # Check cache first
        cached_ts, cached_jobs = _load_cache()
        if cached_jobs and (time.time() - cached_ts) < _CACHE_TTL:
            logger.info(f"📦 Cache hit: {len(cached_jobs)} jobs, {int(time.time()-cached_ts)}s old")
            return cached_jobs[:max_jobs]

        all_jobs = []
        seen = set()

        # Phase 1: JSearch (only 3 queries to conserve API quota)
        jsearch_jobs = self.search_jsearch(max_total=max_jobs)
        for j in jsearch_jobs:
            key = (j["company"].lower(), j["title"].lower())
            if key not in seen:
                seen.add(key)
                all_jobs.append(j)

        # Phase 2: LinkedIn XHR (fill remaining, free unlimited)
        if len(all_jobs) < max_jobs:
            li_jobs = self.search_linkedin_xhr(max_jobs=max_jobs - len(all_jobs))
            for j in li_jobs:
                key = (j["company"].lower(), j["title"].lower())
                if key not in seen:
                    seen.add(key)
                    all_jobs.append(j)

        # Save to cache
        if all_jobs:
            _save_cache(all_jobs)
            logger.info(f"💾 Cache saved: {len(all_jobs)} jobs")

        logger.info(f"PAJobScraper v2: total {len(all_jobs)} jobs")
        return all_jobs[:max_jobs]

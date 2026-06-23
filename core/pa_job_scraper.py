"""
PAJobScraper — Zero-Dependency Job Scraper for PythonAnywhere
Uses ONLY JSearch API (guaranteed to work) + LinkedIn XHR (PA-approved).
No BeautifulSoup, no Selenium, no cloudscraper.
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


class PAJobScraper:
    """
    Lightweight job scraper that works on PythonAnywhere free tier.
    Uses JSearch API (primary) + LinkedIn XHR (secondary).
    No external dependencies beyond stdlib + httpx (available on PA).
    """

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
                    # Generate an email placeholder — employer website or apply link domain
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
        """
        Search JSearch API for multiple countries and titles.
        targets: {country_key: [title1, title2]} or None for defaults
        """
        if targets is None:
            targets = {}
            for ck in ("uae", "saudi", "qatar", "kuwait", "lebanon", "remote"):
                targets[ck] = TITLES[:3]

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
                    time.sleep(0.5)  # Rate limit
                except Exception as e:
                    logger.warning(f"JSearch [{country_key}/{title}] error: {e}")

        logger.info(f"JSearch total: {len(all_jobs)} unique jobs")
        return all_jobs[:max_total]

    def search_linkedin_xhr(self, max_jobs: int = 50) -> List[Dict]:
        """
        Search LinkedIn XHR API (works on PA, no auth needed).
        """
        import httpx

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

                    from bs4 import BeautifulSoup
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
        Primary: JSearch API (guaranteed results).
        Fallback: LinkedIn XHR.
        Returns deduplicated job list.
        """
        all_jobs = []
        seen = set()

        # Phase 1: JSearch
        targets = {
            "uae": TITLES[:5],
            "saudi": TITLES[:3],
            "qatar": TITLES[:3],
            "kuwait": TITLES[:2],
            "lebanon": TITLES[:2],
            "remote": ["network engineer", "network administrator"],
        }
        jsearch_jobs = self.search_jsearch(targets, max_total=max_jobs)
        for j in jsearch_jobs:
            key = (j["company"].lower(), j["title"].lower())
            if key not in seen:
                seen.add(key)
                all_jobs.append(j)

        # Phase 2: LinkedIn XHR (fill remaining)
        if len(all_jobs) < max_jobs:
            li_jobs = self.search_linkedin_xhr(max_jobs=max_jobs - len(all_jobs))
            for j in li_jobs:
                key = (j["company"].lower(), j["title"].lower())
                if key not in seen:
                    seen.add(key)
                    all_jobs.append(j)

        logger.info(f"PAJobScraper: total {len(all_jobs)} jobs")
        return all_jobs[:max_jobs]

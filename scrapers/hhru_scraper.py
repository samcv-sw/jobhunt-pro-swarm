# hh.ru Scraper for JobHunt Pro
# Uses hh.ru public API — no Selenium/headless browser needed
# Async, rate-limited, supports 8 GCC + Lebanon countries

import asyncio
import httpx
import random
import time
import logging
from typing import Any, List, Dict, Optional

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]

HH_API = "https://api.hh.ru"
HH_SEARCH = f"{HH_API}/vacancies"
HH_VACANCY = f"{HH_API}/vacancies"  # + /{id}

MIN_DELAY = 0.35
MAX_DELAY = 0.80

COUNTRY_IDS = {
    "lebanon": 1001,
    "russia": 113,
    "uae": 1007,
    "saudi": 1024,
    "qatar": 1013,
    "kuwait": 1015,
    "bahrain": 1002,
    "oman": 1008,
}


class HHRUScraper:
    """Async hh.ru vacancy scraper using the public hh.ru API.
    
    Usage:
        async with HHRUScraper() as scraper:
            jobs = await scraper.search(["Network Engineer"], country="lebanon", pages=3)
    """

    def __init__(self, proxy_url: Optional[str] = None) -> None:
        self.proxy = proxy_url
        self._last: float = 0.0
        self._sess: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> 'HHRUScraper':
        self._sess = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"},
            proxy=self.proxy,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._sess:
            await self._sess.aclose()

    async def _throttle(self) -> None:
        """Rate-limit requests to respect hh.ru API policy."""
        elapsed = time.time() - self._last
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last = time.time()

    def _ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _country(self, country: str) -> Optional[int]:
        """Fuzzy-match country name to hh.ru area ID."""
        cl = country.lower().strip()
        for k, v in COUNTRY_IDS.items():
            if k in cl or cl in k:
                return v
        return None

    async def search(
        self,
        roles: List[str],
        country: str = "",
        keywords: str = "",
        pages: int = 3,
        per_page: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search hh.ru vacancies.

        Args:
            roles: List of job titles to search for (max 3 used in query)
            country: Country name (maps to hh.ru area ID)
            keywords: Extra keywords prepended to search
            pages: Max pages to fetch
            per_page: Results per page (max 100)

        Returns:
            List of job dicts with keys: title, company, location, url,
            salary, description, source, source_id, published_at
        """
        if not self._sess:
            raise RuntimeError("Use 'async with HHRUScraper() as scraper:' context manager")

        parts = roles[:3]
        if keywords:
            parts.insert(0, keywords)
        q = " OR ".join(f'"{p}"' for p in parts)

        params = {
            "text": q,
            "per_page": min(per_page, 100),
            "page": 0,
            "search_field": "name",
        }
        area_id = self._country(country)
        if area_id:
            params["area"] = area_id

        jobs = []
        for page_num in range(pages):
            await self._throttle()
            params["page"] = page_num

            try:
                r = await self._sess.get(
                    HH_SEARCH,
                    params=params,
                    headers={"User-Agent": self._ua()},
                )
                if r.status_code == 429:
                    logger.warning("hh.ru rate limit (429) hit, sleeping for 60s...")
                    await asyncio.sleep(60)
                    continue
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                logger.error(f"hh.ru error on page {page_num}: {e}", exc_info=True)
                continue

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                # Parse salary
                sal = item.get("salary") or {}
                ss = ""
                if sal:
                    sf = sal.get("from")
                    st = sal.get("to")
                    sc = sal.get("currency", "")
                    if sf and st:
                        ss = f"{sf}-{st} {sc}"
                    elif sf:
                        ss = f"from {sf} {sc}"
                    elif st:
                        ss = f"up to {st} {sc}"

                emp = item.get("employer", {})
                area = item.get("area", {})
                snippet = item.get("snippet", {})

                # Build description from snippet
                desc_parts = []
                if snippet.get("requirement"):
                    desc_parts.append(f"Requirements: {snippet['requirement']}")
                if snippet.get("responsibility"):
                    desc_parts.append(f"Responsibilities: {snippet['responsibility']}")

                experience = item.get("experience", {}).get("name", "")
                employment = item.get("employment", {}).get("name", "")

                full_desc = " | ".join(desc_parts) if desc_parts else ""
                if experience:
                    full_desc = f"[{experience}] {full_desc}"
                if employment:
                    full_desc = f"[{employment}] {full_desc}"

                jobs.append({
                    "title": item.get("name", ""),
                    "company": emp.get("name", ""),
                    "location": area.get("name", ""),
                    "url": item.get("alternate_url", ""),
                    "salary": ss,
                    "description": full_desc[:1000],
                    "source": "hh.ru",
                    "source_id": str(item.get("id", "")),
                    "published_at": item.get("published_at", ""),
                })

            # Stop if we've fetched all available pages
            if page_num + 1 >= data.get("pages", 0):
                break

        return jobs

    async def get_vacancy_detail(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full details for a single vacancy."""
        if not self._sess:
            raise RuntimeError("Use 'async with HHRUScraper() as scraper:' context manager")

        await self._throttle()
        try:
            r = await self._sess.get(
                f"{HH_VACANCY}/{vacancy_id}",
                headers={"User-Agent": self._ua()},
            )
            if r.status_code == 429:
                logger.warning("hh.ru rate limit (429) hit on vacancy detail, sleeping for 60s...")
                await asyncio.sleep(60)
                return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"hh.ru vacancy detail error for ID {vacancy_id}: {e}", exc_info=True)
            return None

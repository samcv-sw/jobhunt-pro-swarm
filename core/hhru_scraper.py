"""
JobHunt Pro — hh.ru Job Scraper (Free REST API, no key required)

hh.ru is the #1 job board in Russia/CIS with a clean, documented, no-auth REST API.
https://api.hh.ru/vacancies returns rich JSON: key_skills, salary with currency,
employer info, detailed descriptions, and pagination up to 2000 results.

Integration: Call search_hhru() from global_scraper.py or directly.
"""

import asyncio
import logging
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from curl_cffi.requests import AsyncSession as httpx_AsyncClient
import httpx

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

HHRU_API_BASE = "https://api.hh.ru"
HHRU_USER_AGENT = "JobHuntPro/16.0 (samsalameh.cv@gmail.com)"  # Required by hh.ru TOS

# API limit: per_page max 100, max 2000 results total (pages 0-19)
HHRU_PER_PAGE = 100
HHRU_MAX_RESULTS = 2000
HHRU_INTER_PAGE_DELAY = 0.5  # seconds — polite, no API key rate limit

# ═══════════════════════════════════════════════════════════════════════════════
# Location Name → hh.ru Area ID Mapper
# ═══════════════════════════════════════════════════════════════════════════════

# hh.ru area hierarchy: country > region > city
# Area IDs are stable and documented at https://api.hh.ru/areas
HHRU_AREA_MAP: Dict[str, int] = {
    # ── Russia ──
    "russia": 113,
    "россия": 113,
    "rf": 113,
    # Russia — major cities
    "moscow": 1,
    "москва": 1,
    "saint petersburg": 2,
    "st. petersburg": 2,
    "st petersburg": 2,
    "spb": 2,
    "санкт-петербург": 2,
    "питер": 2,
    "novosibirsk": 4,
    "новосибирск": 4,
    "yekaterinburg": 3,
    "екатеринбург": 3,
    "ekaterinburg": 3,
    "kazan": 88,
    "казань": 88,
    "nizhny novgorod": 66,
    "нижний новгород": 66,
    "chelyabinsk": 104,
    "челябинск": 104,
    "samara": 78,
    "самара": 78,
    "omsk": 68,
    "омск": 68,
    "rostov-on-don": 76,
    "rostov on don": 76,
    "ростов-на-дону": 76,
    "ufa": 99,
    "уфа": 99,
    "krasnoyarsk": 49,
    "красноярск": 49,
    "voronezh": 26,
    "воронеж": 26,
    "perm": 72,
    "пермь": 72,
    "volgograd": 24,
    "волгоград": 24,
    "krasnodar": 53,
    "краснодар": 53,
    "saratov": 79,
    "саратов": 79,
    "tyumen": 95,
    "тюмень": 95,
    "togliatti": 91,
    "тольятти": 91,
    "izhevsk": 42,
    "ижевск": 42,
    "barnaul": 14,
    "барнаул": 14,
    "ulyanovsk": 98,
    "ульяновск": 98,
    "irkutsk": 40,
    "иркутск": 40,
    "khabarovsk": 102,
    "хабаровск": 102,
    "vladivostok": 22,
    "владивосток": 22,
    "yaroslavl": 112,
    "ярославль": 112,
    "tomsk": 90,
    "томск": 90,
    "orenburg": 69,
    "оренбург": 69,
    "kemerovo": 44,
    "кемерово": 44,
    "novokuznetsk": 67,
    "новокузнецк": 67,
    "ryazan": 77,
    "рязань": 77,
    "astrakhan": 12,
    "астрахань": 12,
    "naberezhnye chelny": 65,
    "набережные челны": 65,
    "penza": 71,
    "пенза": 71,
    "lipetsk": 58,
    "липецк": 58,
    "kirov": 46,
    "киров": 46,
    "cheboksary": 105,
    "чебоксары": 105,
    "tula": 94,
    "тула": 94,
    "kaliningrad": 43,
    "калининград": 43,
    "bryansk": 16,
    "брянск": 16,
    "kursk": 55,
    "курск": 55,
    "tver": 89,
    "тверь": 89,
    "ivanovo": 39,
    "иваново": 39,
    "magnitogorsk": 59,
    "магнитогорск": 59,
    "sochi": 237,
    "сочи": 237,
    "belgorod": 15,
    "белгород": 15,
    "surgut": 86,
    "сургут": 86,
    "nizhny tagil": 70,
    "нижний тагил": 70,
    "arkhangelsk": 11,
    "архангельск": 11,
    "stavropol": 85,
    "ставрополь": 85,
    "murmansk": 64,
    "мурманск": 64,
    "smolensk": 83,
    "смоленск": 83,

    # ── Kazakhstan ──
    "kazakhstan": 40,
    "казахстан": 40,
    "almaty": 160,
    "алматы": 160,
    "nur-sultan": 164,
    "nursultan": 164,
    "astana": 164,
    "астана": 164,
    "нур-султан": 164,
    "shymkent": 177,
    "чимкент": 177,
    "шимкент": 177,
    "karaganda": 163,
    "караганда": 163,
    "aktobe": 158,
    "актобе": 158,
    "atyrau": 159,
    "атырау": 159,

    # ── Belarus ──
    "belarus": 16,
    "беларусь": 16,
    "белоруссия": 16,
    "minsk": 1002,
    "минск": 1002,
    "gomel": 1004,
    "гомель": 1004,
    "mogilev": 1009,
    "могилев": 1009,
    "могилёв": 1009,
    "vitebsk": 1015,
    "витебск": 1015,
    "grodno": 1005,
    "гродно": 1005,
    "brest": 1003,
    "брест": 1003,

    # ── Other CIS countries ──
    "uzbekistan": 97,
    "tashkent": 2759,
    "azerbaijan": 9,
    "baku": 1518,
    "armenia": 13,
    "yerevan": 1817,
    "georgia": 28,
    "tbilisi": 1837,
    "kyrgyzstan": 48,
    "bishkek": 1844,
    "moldova": 62,
    "chisinau": 1806,
    "ukraine": 5,
    "kyiv": 115,
    "kiev": 115,
    "kharkiv": 121,
    "odesa": 110,
    "odessa": 110,
    "dnipro": 106,
    "lviv": 108,

    # ── Special ──
    "remote": 0,
    "удаленно": 0,
    "удалённо": 0,
    "удаленная работа": 0,
    "worldwide": 0,
    "anywhere": 0,
    "work from home": 0,
    "wfh": 0,
}


def resolve_area_id(location: str) -> Optional[int]:
    """Resolve a location name to an hh.ru area ID.

    Tries: exact match → lowercase match → partial match in keys.
    Returns None if no match (caller can ignore or fall back to no filter).
    """
    if not location:
        return None

    loc = location.strip()
    loc_lower = loc.lower()

    # Exact match (case-insensitive)
    for key, area_id in HHRU_AREA_MAP.items():
        if key.lower() == loc_lower:
            return area_id

    # Check if a key contains the location (e.g., "dubai" won't match but
    # "saint petersburg" contains "petersburg")
    for key, area_id in HHRU_AREA_MAP.items():
        if loc_lower in key.lower():
            return area_id

    # Check if the location contains a key (e.g., "Moscow, Russia")
    for key, area_id in HHRU_AREA_MAP.items():
        if key.lower() in loc_lower:
            return area_id

    return None


def resolve_area_ids(locations: List[str]) -> List[int]:
    """Resolve a list of location names to hh.ru area IDs.

    Deduplicates and filters out None values.
    """
    ids: List[int] = []
    seen: set = set()
    for loc in locations:
        area_id = resolve_area_id(loc)
        if area_id is not None and area_id not in seen:
            seen.add(area_id)
            ids.append(area_id)
    return ids


# ═══════════════════════════════════════════════════════════════════════════════
# Salary Parser
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_hhru_salary(salary_raw: Optional[Dict]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Parse hh.ru salary JSON block into (min, max, currency).

    hh.ru format:
    {
        "from": 100000,
        "to": 150000,
        "currency": "RUR",
        "gross": false
    }
    """
    if not salary_raw:
        return None, None, None

    salary_min = salary_raw.get("from")
    salary_max = salary_raw.get("to")
    currency = salary_raw.get("currency", "").upper()

    # Convert numeric types
    if salary_min is not None:
        salary_min = float(salary_min)
    if salary_max is not None:
        salary_max = float(salary_max)

    return salary_min, salary_max, currency if currency else None


# ═══════════════════════════════════════════════════════════════════════════════
# Job Dict Builder
# ═══════════════════════════════════════════════════════════════════════════════

def _build_job(job_data: Dict) -> Dict:
    """Convert a raw hh.ru vacancy JSON dict into JobHunt Pro's job schema.

    Returns dict with keys:
        title, company, location, description, url, salary_min, salary_max,
        salary_currency, posted_date, source: "hh.ru", skills: [],
        job_id (for dedup), snippet, email, all_emails, country
    """
    title = (job_data.get("name") or "").strip()

    # Employer
    employer = job_data.get("employer") or {}
    company = (employer.get("name") or "Unknown").strip()

    # Location
    area = job_data.get("area") or {}
    location = (area.get("name") or "").strip()

    # URL
    alternate_url = job_data.get("alternate_url") or ""
    job_id_str = job_data.get("id", "")
    if not alternate_url and job_id_str:
        alternate_url = f"https://hh.ru/vacancy/{job_id_str}"
    url = alternate_url

    # Salary
    salary_min, salary_max, salary_currency = _parse_hhru_salary(job_data.get("salary"))

    # Skills (key_skills array from hh.ru)
    skills = []
    key_skills = job_data.get("key_skills") or []
    for skill_obj in key_skills:
        skill_name = skill_obj.get("name", "").strip()
        if skill_name:
            skills.append(skill_name)

    # Published date
    published_at = job_data.get("published_at") or ""
    posted_date = published_at  # ISO format from API

    # Description (snippet from hh.ru)
    snippet_data = job_data.get("snippet") or {}
    snippet = ""
    if snippet_data:
        requirement = (snippet_data.get("requirement") or "").strip()
        responsibility = (snippet_data.get("responsibility") or "").strip()
        parts = [p for p in [requirement, responsibility] if p]
        snippet = " | ".join(parts)

    # Full description via separate API call is expensive; use snippet.
    # The full description is available at https://api.hh.ru/vacancies/{id}
    # but requires an extra HTTP call per job.
    description = snippet

    # Company domain for email placeholder
    company_domain = re.sub(r"[^a-z0-9]", "", company.lower())
    placeholder_email = f"careers@{company_domain}.com" if company_domain else ""

    job = {
        "job_id": _make_job_id(title, company, url),
        "title": title,
        "company": company,
        "email": placeholder_email,
        "all_emails": [placeholder_email] if placeholder_email else [],
        "location": location,
        "snippet": snippet[:500],
        "description": description[:1000],
        "source": "hh.ru",
        "url": url,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "posted_date": posted_date,
        "skills": skills,
        "country": "ru",  # hh.ru is primarily Russia/CIS
    }
    return job


def _make_job_id(title: str, company: str, url: str = "") -> str:
    """Generate unique job ID matching the rest of JobHunt Pro."""
    raw = f"{title.lower().strip()}:{company.lower().strip()}:{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════════════════
# Main Search Function
# ═══════════════════════════════════════════════════════════════════════════════

async def search_hhru(
    job_titles: List[str],
    locations: List[str],
    limit: int = 100,
    max_pages: int = 20,  # 20 pages × 100 per page = 2000 max
    delay_between_pages: float = HHRU_INTER_PAGE_DELAY,
) -> List[Dict]:
    """Search hh.ru for jobs matching given titles and locations.

    Uses the free, no-key hh.ru REST API (https://api.hh.ru/vacancies).
    Handles pagination, rate limiting, and returns JobHunt Pro schema dicts.

    Args:
        job_titles: List of job titles to search for (e.g., ["network engineer", "системный администратор"])
        locations: List of location names (e.g., ["Moscow", "Russia", "Almaty"])
        limit: Maximum number of results to return (default 100)
        max_pages: Maximum pages to fetch (default 20, API limit is 2000 results)
        delay_between_pages: Seconds to wait between pages (default 0.5s)

    Returns:
        List of job dicts with keys: title, company, location, description, url,
        salary_min, salary_max, salary_currency, posted_date, source, skills, job_id, ...
    """
    # Resolve locations to area IDs
    area_ids = resolve_area_ids(locations)

    if not area_ids:
        logger.info("hh.ru: No hh.ru area IDs matched for locations: %s — searching without area filter", locations)
    else:
        logger.info("hh.ru: Resolved locations %s → area IDs %s", locations, area_ids)

    all_jobs: List[Dict] = []
    seen_ids: set = set()

    async with httpx_AsyncClient(impersonate='chrome120', timeout=30.0, headers={
        "User-Agent": HHRU_USER_AGENT,
    }) as client:
        for title in job_titles:
            if len(all_jobs) >= limit:
                break

            title = title.strip()
            if not title:
                continue

            logger.info("hh.ru: Searching '%s' (collected %d so far)...", title, len(all_jobs))

            # Search with each area ID
            for area_id in (area_ids or [None]):
                if len(all_jobs) >= limit:
                    break

                jobs_for_query = await _search_single(
                    client=client,
                    text=title,
                    area_id=area_id,
                    max_pages=max_pages,
                    delay=delay_between_pages,
                    limit=limit - len(all_jobs),
                )

                for job in jobs_for_query:
                    jid = job.get("job_id", "")
                    if jid and jid not in seen_ids:
                        seen_ids.add(jid)
                        all_jobs.append(job)
                        if len(all_jobs) >= limit:
                            break

    logger.info("hh.ru: Search complete — %d unique jobs found", len(all_jobs))
    return all_jobs[:limit]


async def _search_single(
    client: httpx.AsyncClient,
    text: str,
    area_id: Optional[int],
    max_pages: int,
    delay: float,
    limit: int,
) -> List[Dict]:
    """Search a single (text, area_id) combination across pages."""
    jobs: List[Dict] = []

    for page in range(max_pages):
        if len(jobs) >= limit:
            break

        params = {
            "text": text,
            "per_page": HHRU_PER_PAGE,
            "page": page,
            "search_field": "name",  # Search in job title only
            "order_by": "publication_time",
        }
        if area_id is not None:
            params["area"] = area_id

        try:
            response = await client.get(
                f"{HHRU_API_BASE}/vacancies",
                params=params,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning("hh.ru: Rate limited (429) — waiting %ds", retry_after)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code != 200:
                logger.warning("hh.ru: HTTP %d for text='%s' area=%s page=%d",
                               response.status_code, text, area_id, page)
                # Likely no more results or invalid params
                if response.status_code == 400:
                    break
                continue

            data = response.json()

            items = data.get("items", [])
            if not items:
                # No more results
                break

            for item in items:
                job = _build_job(item)
                if job:
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break

            # Check if we've reached the end
            total_pages = data.get("pages", 0)
            if page + 1 >= total_pages:
                break

            # Polite delay between pages
            if page < max_pages - 1:
                await asyncio.sleep(delay)

        except httpx.TimeoutException:
            logger.warning("hh.ru: Timeout for text='%s' area=%s page=%d", text, area_id, page)
            await asyncio.sleep(delay * 2)
            continue
        except httpx.HTTPError as e:
            logger.warning("hh.ru: HTTP error for text='%s' area=%s page=%d: %s", text, area_id, page, e)
            break
        except Exception as e:
            logger.error("hh.ru: Unexpected error: %s", e)
            break

    return jobs


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience: Sync Wrapper (for use in synchronous GlobalJobScraper context)
# ═══════════════════════════════════════════════════════════════════════════════

def search_hhru_sync(
    job_titles: List[str],
    locations: List[str],
    limit: int = 100,
    max_pages: int = 20,
    delay_between_pages: float = HHRU_INTER_PAGE_DELAY,
) -> List[Dict]:
    """Synchronous wrapper around search_hhru().

    Use when calling from non-async code (e.g., GlobalJobScraper).
    """
    import asyncio as _asyncio

    try:
        # If already in an event loop, use run_in_executor approach
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context — create a new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    _asyncio.run,
                    search_hhru(
                        job_titles=job_titles,
                        locations=locations,
                        limit=limit,
                        max_pages=max_pages,
                        delay_between_pages=delay_between_pages,
                    ),
                )
                return future.result()
        else:
            return loop.run_until_complete(
                search_hhru(
                    job_titles=job_titles,
                    locations=locations,
                    limit=limit,
                    max_pages=max_pages,
                    delay_between_pages=delay_between_pages,
                )
            )
    except RuntimeError:
        # No event loop at all
        return _asyncio.run(
            search_hhru(
                job_titles=job_titles,
                locations=locations,
                limit=limit,
                max_pages=max_pages,
                delay_between_pages=delay_between_pages,
            )
        )


# ═══════════════════════════════════════════════════════════════════════════════
# hh.ru AREA Discovery (Dynamic — fetch from API)
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_area_tree() -> Dict:
    """Fetch the full hh.ru area tree.

    https://api.hh.ru/areas returns a nested country→region→city tree.
    Useful for discovering new area IDs or building a comprehensive mapper.
    """
    try:
        async with httpx_AsyncClient(impersonate='chrome120', timeout=30.0, headers={
            "User-Agent": HHRU_USER_AGENT,
        }) as client:
            response = await client.get(f"{HHRU_API_BASE}/areas")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error("hh.ru: Failed to fetch area tree: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Sanity Check / Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async def _quick_test():
        print("=" * 60)
        print("hh.ru Scraper — Quick Test")
        print("=" * 60)

        # Test 1: Search for network engineer in Moscow
        print("\n--- Test: 'network engineer' in Moscow (limit=5) ---")
        jobs = await search_hhru(
            job_titles=["network engineer"],
            locations=["Moscow"],
            limit=5,
            max_pages=2,
        )
        for i, j in enumerate(jobs, 1):
            print(f"  {i}. {j['title']} @ {j['company']} — {j['location']}")
            print(f"     Salary: {j['salary_min']}-{j['salary_max']} {j['salary_currency']}")
            print(f"     Skills: {j['skills']}")
            print(f"     URL: {j['url']}")
        print(f"  → Found {len(jobs)} jobs")

        # Test 2: Search with Russian keywords
        print("\n--- Test: 'системный администратор' in Russia (limit=5) ---")
        jobs2 = await search_hhru(
            job_titles=["системный администратор"],
            locations=["Russia"],
            limit=5,
            max_pages=2,
        )
        for i, j in enumerate(jobs2, 1):
            print(f"  {i}. {j['title']} @ {j['company']} — {j['location']}")
        print(f"  → Found {len(jobs2)} jobs")

        # Test 3: Location resolution
        print("\n--- Test: Location resolution ---")
        test_locs = ["Moscow", "Almaty", "Minsk", "SPB", "Dubai", "remote", "казань"]
        for loc in test_locs:
            aid = resolve_area_id(loc)
            print(f"  {loc:20s} → area_id={aid}")

    asyncio.run(_quick_test())

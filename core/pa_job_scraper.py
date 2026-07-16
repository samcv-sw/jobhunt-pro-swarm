"""
PAJobScraper v4 — GLOBAL SCALE (v18.0)
- JSearch API with smart caching (2h TTL) to conserve 300/month quota
- hh.ru FREE REST API (Russia/CIS market — no key needed)
- Indeed FREE RSS feeds (no blocks, no API key)
- Glassdoor free job listing scraper (best-effort)
- LinkedIn XHR as fallback
- Remotive FREE API (worldwide remote, no key)
- Arbeitnow FREE API (Europe, no key)
- RemoteOK FREE API (worldwide remote, no key)
- WeWorkRemotely RSS (free, reliable)
- The Muse API (free, global companies, no key)
- Jobicy FREE API (remote-first, no key)
- Rotating queries: 3 random locations + 2 random titles per tick
  covers all ~50 locations over ~15 ticks (1 hour)
- Exponential backoff on all HTTP fetches
- Per-source circuit-breaker (3 failures → 30 min cooldown)
- URL-based deduplication (on top of company+title)
"""

import json
import logging
import os
import random
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

import config

logger = logging.getLogger(__name__)

# JSearch API config
JSEARCH_KEY = os.getenv("JSEARCH_API_KEY")
JSEARCH_BACKUP = os.getenv("JSEARCH_BACKUP_KEY") or os.getenv("JSEARCH_API_KEY_BACKUP")

# ── Country Mapping ──────────────────────────────────────────────────────
COUNTRIES = {
    # GCC (all 6)
    "lebanon": "lb",
    "uae": "ae",
    "saudi": "sa",
    "qatar": "qa",
    "kuwait": "kw",
    "oman": "om",
    "bahrain": "bh",
    # MENA
    "jordan": "jo",
    "egypt": "eg",
    "morocco": "ma",
    "tunisia": "tn",
    "iraq": "iq",
    "syria": "sy",
    # ASIA
    "india": "in",
    "singapore": "sg",
    "malaysia": "my",
    # EUROPE
    "uk": "gb",
    "germany": "de",
    "netherlands": "nl",
    "ireland": "ie",
    "poland": "pl",
    "portugal": "pt",
    "spain": "es",
    # Turkey
    "turkey": "tr",
    # Remote
    "remote": "",
}

# ── City Mapping (used for display / LinkedIn / Indeed RSS) ─────────────
CITIES = {
    # GCC
    "lebanon": "Beirut",
    "uae": "Dubai",
    "saudi": "Riyadh",
    "qatar": "Doha",
    "kuwait": "Kuwait City",
    "oman": "Muscat",
    "bahrain": "Manama",
    # MENA
    "jordan": "Amman",
    "egypt": "Cairo",
    "morocco": "Casablanca",
    "tunisia": "Tunis",
    "iraq": "Baghdad",
    "syria": "Damascus",
    # ASIA
    "india": "Mumbai",
    "singapore": "Singapore",
    "malaysia": "Kuala Lumpur",
    # EUROPE
    "uk": "London",
    "germany": "Berlin",
    "netherlands": "Amsterdam",
    "ireland": "Dublin",
    "poland": "Warsaw",
    "portugal": "Lisbon",
    "spain": "Madrid",
    # Turkey
    "turkey": "Istanbul",
    # Remote
    "remote": "",
}

# ── Job Titles for Rotation ─────────────────────────────────────────────
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
    "noc engineer",
    "cybersecurity engineer",
    "cloud network engineer",
    "devops engineer",
    "cisco engineer",
    "senior network engineer",
]

# ── Indeed RSS per-country locations ────────────────────────────────────
INDEED_RSS_LOCATIONS = {
    "uae": "Dubai, AE",
    "saudi": "Riyadh, SA",
    "qatar": "Doha, QA",
    "kuwait": "Kuwait City, KW",
    "oman": "Muscat, OM",
    "bahrain": "Manama, BH",
    "lebanon": "Beirut, LB",
    "jordan": "Amman, JO",
    "egypt": "Cairo, EG",
    "morocco": "Casablanca, MA",
    "tunisia": "Tunis, TN",
    "iraq": "Baghdad, IQ",
    "india": "Mumbai, IN",
    "singapore": "Singapore, SG",
    "malaysia": "Kuala Lumpur, MY",
    "uk": "London, GB",
    "germany": "Berlin, DE",
    "netherlands": "Amsterdam, NL",
    "ireland": "Dublin, IE",
    "poland": "Warsaw, PL",
    "portugal": "Lisbon, PT",
    "spain": "Madrid, ES",
    "turkey": "Istanbul, TR",
}

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")
# Source-specific TTLs in seconds
_SOURCE_TTLS = {
    "jsearch": 7200,
    "hhru": 3600,
    "indeed_rss": 1800,
    "glassdoor": 3600,
    "linkedin_xhr": 10800,
    "remotive": 3600,
    "arbeitnow": 3600,
    "remoteok": 1800,
    "weworkremotely": 1800,
    "themuse": 7200,
    "jobicy": 3600,
}
_CACHE_TTL = 7200  # Default global cache TTL in seconds (2 hours)

# ── Per-source circuit-breaker state ─────────────────────────────────────
_SOURCE_FAILURES: dict = {}  # source_key -> consecutive_failure_count
_SOURCE_DISABLED_UNTIL: dict = {}  # source_key -> epoch_timestamp
_CIRCUIT_FAILURE_THRESHOLD = 3  # failures before cooldown
_CIRCUIT_COOLDOWN_SECONDS = 1800  # 30-minute cooldown


def _source_is_healthy(source_key: str) -> bool:
    """Return False if source is currently in cooldown (circuit open)."""
    until = _SOURCE_DISABLED_UNTIL.get(source_key, 0)
    return time.time() >= until


def _record_source_failure(source_key: str):
    """Increment failure counter; open circuit after threshold."""
    count = _SOURCE_FAILURES.get(source_key, 0) + 1
    _SOURCE_FAILURES[source_key] = count
    if count >= _CIRCUIT_FAILURE_THRESHOLD:
        _SOURCE_DISABLED_UNTIL[source_key] = time.time() + _CIRCUIT_COOLDOWN_SECONDS
        logger.warning(
            f"[Circuit] {source_key} disabled for {_CIRCUIT_COOLDOWN_SECONDS // 60} min after {count} consecutive failures"
        )


def _record_source_success(source_key: str):
    """Reset circuit counter on success."""
    _SOURCE_FAILURES[source_key] = 0
    _SOURCE_DISABLED_UNTIL.pop(source_key, None)


def _load_cache():
    """Load merged cache from all per-source files (backward compat)."""
    try:
        merged = []
        latest_ts = 0
        cache_dir = _CACHE_DIR
        if not os.path.exists(cache_dir):
            return 0, []
        now = time.time()
        for fname in os.listdir(cache_dir):
            if not fname.endswith(".json"):
                continue
            source_key = fname.replace(".json", "")
            ttl = _SOURCE_TTLS.get(source_key, 7200)
            fpath = os.path.join(cache_dir, fname)
            try:
                with open(fpath) as f:
                    data = json.load(f)
                ts = data.get("ts", 0)
                if (now - ts) < ttl:
                    merged.extend(data.get("jobs", []))
                    if ts > latest_ts:
                        latest_ts = ts
            except Exception as e:
                logger.debug(f"[_load_cache] Error parsing file {fpath}: {e}")
        return latest_ts, merged
    except Exception as e:
        logger.debug(f"[_load_cache] Error reading cache dir: {e}")
    return 0, []


def _save_cache(jobs):
    """Save to per-source cache files with individual TTLs."""
    try:
        cache_dir = _CACHE_DIR
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        # Group jobs by source
        by_source = {}
        for j in jobs:
            src = j.get("source", "unknown")
            by_source.setdefault(src, []).append(j)
        now = time.time()
        for src, src_jobs in by_source.items():
            fpath = os.path.join(cache_dir, f"{src}.json")
            with open(fpath, "w") as f:
                json.dump({"ts": now, "jobs": src_jobs}, f)
    except Exception as e:
        logger.debug(f"[_save_cache] Error saving to cache: {e}")


# ── Rotation Helper ─────────────────────────────────────────────────────
_ALL_COUNTRY_KEYS = list(COUNTRIES.keys())
_ROTATION_TICK = 0


def _get_rotation_selection(n_locations: int = 3, n_titles: int = 2):
    """Return (selected_countries, selected_titles) rotating per tick."""
    global _ROTATION_TICK

    # Seed rotation deterministically from tick index so different
    # scraper instances don't all pick the same random selection.
    rng = random.Random(_ROTATION_TICK + int(time.time() // 300))
    _ROTATION_TICK = (_ROTATION_TICK + 1) % 10000

    # Pick random countries
    pool = list(_ALL_COUNTRY_KEYS)
    rng.shuffle(pool)
    selected_countries = pool[:n_locations]

    # Pick random titles
    title_pool = list(TITLES)
    rng.shuffle(title_pool)
    selected_titles = title_pool[:n_titles]

    return selected_countries, selected_titles


def _clean_email(company: str, url: str = None) -> str:
    """Intelligently clean company name or URL to generate a valid domain email,
    stripping common subdomains (www, careers, jobs, app, portal, etc.).
    """
    import re
    from urllib.parse import urlparse

    domain = ""
    # Try parsing domain from URL first if available
    if url and url.startswith("http"):
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            for sub in [
                "www.",
                "careers.",
                "jobs.",
                "recruiting.",
                "app.",
                "apply.",
                "portal.",
            ]:
                if netloc.startswith(sub):
                    netloc = netloc[len(sub) :]
            if "." in netloc and len(netloc) > 4:
                domain = netloc
        except Exception as e:
            logger.debug(f"[_clean_email] URL parse fallback: {e}")

    # Fallback to company name normalization
    if not domain:
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", company).lower()
        if clean_name:
            domain = f"{clean_name}.com"

    if domain:
        # Prevent double-generation of careers@careers.
        if domain.startswith("careers."):
            domain = domain[8:]
        elif domain.startswith("jobs."):
            domain = domain[5:]
        return f"careers@{domain}"
    return ""


# ══════════════════════════════════════════════════════════════════════════
# PAJobScraper
# ══════════════════════════════════════════════════════════════════════════


class PAJobScraper:
    def __init__(self):
        # Filter out unset keys so rotation never sends None
        self.jsearch_keys = [k for k in (JSEARCH_KEY, JSEARCH_BACKUP) if k]
        self._key_idx = 0
        self._hhru_user_agent = "JobHuntPro/17.0 (samsalameh.cv@gmail.com)"

    def _fetch_url(
        self, url: str, headers: dict = None, timeout: int = 15, retries: int = 3
    ) -> str:
        """Fetch URL with exponential backoff, routing through Cloudflare Worker first."""
        last_exc = None
        for attempt in range(retries):
            try:
                return self._fetch_url_once(url, headers=headers, timeout=timeout)
            except Exception as exc:
                last_exc = exc
                if attempt < retries - 1:
                    wait = (2**attempt) + random.uniform(0, 1)
                    logger.debug(
                        f"[_fetch_url] attempt {attempt + 1} failed ({exc}), retrying in {wait:.1f}s"
                    )
                    time.sleep(wait)
        raise last_exc

    def _fetch_url_once(self, url: str, headers: dict = None, timeout: int = 15) -> str:
        """Single-attempt URL fetch routing through Cloudflare Worker scrape endpoint, falling back to direct request."""
        worker_url = os.getenv(
            "WORKER_URL", config.WORKER_URL
        )
        scrape_url = f"{worker_url.rstrip('/')}/scrape?url={urllib.request.quote(url)}"

        logger.info(f"[PAJobScraper] Routing request via Cloudflare Worker: {url}")
        try:
            req = urllib.request.Request(
                scrape_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                if isinstance(data, dict) and "content" in data:
                    content = data["content"]
                    if content:
                        content_lower = content.lower()
                        block_indicators = [
                            "cf-challenge",
                            "cf-cookie-error",
                            "cf-browser-verification",
                            "attention required! | cloudflare",
                            "cloudflare ray id",
                            "ray id:",
                            "captcha-bypass",
                            "hcaptcha",
                            "recaptcha",
                        ]
                        if any(ind in content_lower for ind in block_indicators):
                            logger.warning(
                                f"[PAJobScraper] Worker request for {url} returned a Cloudflare block page. Falling back to direct request."
                            )
                        else:
                            logger.info(
                                f"[PAJobScraper] Successfully fetched {len(content)} bytes via Worker."
                            )
                            return content
                if isinstance(data, dict) and "error" in data:
                    logger.warning(
                        f"[PAJobScraper] Worker scrape returned error: {data['error']}"
                    )
        except Exception as e:
            logger.warning(
                f"[PAJobScraper] Worker scrape failed: {e}. Falling back to direct request."
            )

        # Fallback to direct request using curl_cffi for perfect TLS impersonation
        logger.info(f"[PAJobScraper] Direct fallback request with curl_cffi: {url}")
        try:
            from curl_cffi import requests as cffi_requests

            if not headers:
                headers = {}
            if "User-Agent" not in headers:
                headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            # Organic Warmup: Hit root domain first if we expect Cloudflare
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                logger.info(f"[PAJobScraper] Organic warmup for {root_url}")
                session = cffi_requests.Session(impersonate="chrome120")
                session.get(root_url, timeout=10)
            except Exception as w_exc:
                logger.debug(f"[PAJobScraper] Warmup failed, ignoring: {w_exc}")
                session = cffi_requests.Session(impersonate="chrome120")

            resp = session.get(url, headers=headers, timeout=timeout)
            return resp.text
        except ImportError:
            logger.warning("[PAJobScraper] curl_cffi not installed, falling back to urllib (HIGH BAN RISK)")
            if not headers or "User-Agent" not in headers:
                import random
                UAS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36"]
                if not headers:
                    headers = {}
                headers["User-Agent"] = random.choice(UAS)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")

    # ══════════════════════════════════════════════════════════════════════
    # JSearch API (kept for backward compatibility)
    # ══════════════════════════════════════════════════════════════════════

    def _jsearch_request(
        self, query: str, country_code: str = "", page: int = 1
    ) -> list[dict]:
        """Make JSearch API request with key rotation."""
        if not self.jsearch_keys:
            logger.warning("JSearch API keys not configured; skipping JSearch request")
            return []
        for attempt in range(len(self.jsearch_keys)):
            key = self.jsearch_keys[self._key_idx % len(self.jsearch_keys)]
            self._key_idx += 1
            try:
                url = f"{config.JSEARCH_API_URL}?query={urllib.request.quote(query)}&page={page}&num_pages=1"
                if country_code:
                    url += f"&country={country_code}"
                req = urllib.request.Request(
                    url,
                    headers={
                        "X-RapidAPI-Key": key,
                        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                        "User-Agent": "Mozilla/5.0",
                    },
                )
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
                        email = _clean_email(employer, employer_website)
                    else:
                        email = _clean_email(employer, apply_link)
                    if employer and title:
                        jobs.append(
                            {
                                "id": f"jsearch_{j.get('job_id', str(time.time()))}",
                                "title": title[:100],
                                "company": employer[:80],
                                "location": f"{city}, {country}"[:60]
                                if city
                                else country[:60],
                                "source": "jsearch",
                                "url": apply_link,
                                "email": email,
                                "snippet": description[:200],
                                "job_id": j.get("job_id", ""),
                            }
                        )
                return jobs
            except Exception as e:
                logger.warning(f"JSearch attempt {attempt + 1} failed: {e}")
                continue
        return []

    def search_jsearch(
        self,
        targets: dict[str, list[str]] = None,
        max_total: int = 100,
        query: str = "",
        location: str = "",
    ) -> list[dict]:
        """Search JSearch API — OPTIMIZED: only 3 queries per call (not 15)."""
        if targets is None:
            if query or location:
                # Map location to country key
                country_key = "uae"  # Default
                if location:
                    loc_lower = location.lower()
                    for k in COUNTRIES:
                        if k in loc_lower or loc_lower in k:
                            country_key = k
                            break
                targets = {country_key: [query or "network engineer"]}
            else:
                # Rotating: pick 3 random country+title pairs
                selected_countries, selected_titles = _get_rotation_selection(3, 2)
                targets = {}
                for ck in selected_countries:
                    for title in selected_titles:
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

    # ══════════════════════════════════════════════════════════════════════
    # hh.ru FREE REST API (Russia/CIS — no key needed)
    # ══════════════════════════════════════════════════════════════════════

    def _parse_hhru_item(self, item: dict, area_name: str) -> dict | None:
        """Parse a single vacancy item from hh.ru API response."""
        job_title = (item.get("name") or "").strip()
        employer = item.get("employer") or {}
        company = (employer.get("name") or "Unknown").strip()
        area = item.get("area") or {}
        location = (area.get("name") or area_name).strip()
        alternate_url = item.get("alternate_url") or ""
        job_id_str = item.get("id", "")
        if not alternate_url and job_id_str:
            alternate_url = f"{config.HH_RU_VACANCY_BASE_URL}/{job_id_str}"

        # Salary parsing
        salary_raw = item.get("salary")
        salary_str = ""
        if salary_raw:
            _from = salary_raw.get("from")
            _to = salary_raw.get("to")
            _curr = salary_raw.get("currency", "")
            if _from and _to:
                salary_str = f"{_from}-{_to} {_curr}"
            elif _from:
                salary_str = f"from {_from} {_curr}"
            elif _to:
                salary_str = f"up to {_to} {_curr}"

        # Snippet
        snippet_data = item.get("snippet") or {}
        requirement = (snippet_data.get("requirement") or "").strip()
        responsibility = (snippet_data.get("responsibility") or "").strip()
        parts = [p for p in [requirement, responsibility] if p]
        snippet = " | ".join(parts)[:300]

        # Skills
        skills = []
        for skill_obj in item.get("key_skills") or []:
            sname = skill_obj.get("name", "").strip()
            if sname:
                skills.append(sname)

        if not job_title or not company:
            return None

        jid = f"hhru_{job_id_str}"
        email = _clean_email(company, alternate_url)

        return {
            "id": jid,
            "title": job_title[:100],
            "company": company[:80],
            "location": location[:60],
            "source": "hhru",
            "url": alternate_url,
            "email": email,
            "snippet": snippet[:200],
            "job_id": job_id_str,
            "salary": salary_str,
            "skills": skills,
        }

    def search_hhru(
        self, max_jobs: int = 100, query: str = "", location: str = ""
    ) -> list[dict]:
        """
        Search hh.ru for network engineering roles in Russia/CIS.
        Uses the FREE, no-key hh.ru REST API: https://api.hh.ru/vacancies

        Rate limit: 1 request per 0.5s (hh.ru has no hard limit for polite usage).
        """
        all_jobs = []
        seen_ids = set()

        # hh.ru area IDs for Russia + CIS countries
        hhru_targets = [
            # (area_id, area_name, search_text)
            (1, "Moscow", "network engineer"),
            (1, "Moscow", "инженер сети"),
            (2, "Saint Petersburg", "network engineer"),
            (2, "Saint Petersburg", "сетевой инженер"),
            (113, "Russia (all)", "network engineer"),
            (113, "Russia (all)", "системный администратор"),
            (160, "Almaty", "network engineer"),
            (40, "Kazakhstan", "инженер сети"),
            (1002, "Minsk", "network engineer"),
            (16, "Belarus", "системный администратор"),
            (97, "Uzbekistan", "network engineer"),
            (2759, "Tashkent", "сетевой инженер"),
            (9, "Azerbaijan", "network engineer"),
            (1518, "Baku", "IT инженер"),
        ]

        search_text_input = query or "network engineer"
        targets = []
        if location:
            loc_lower = location.lower()
            for tid, name, _text in hhru_targets:
                if name.lower() in loc_lower or loc_lower in name.lower():
                    # Preserve target with user's query
                    targets.append((tid, name, search_text_input))
            if not targets:
                # Default to entire Russia/CIS search if not matched
                targets = [(113, "Russia (all)", search_text_input)]
        else:
            # If no location specified, use standard targets but replace query if provided
            if query:
                targets = [(tid, name, query) for tid, name, text in hhru_targets]
            else:
                targets = hhru_targets

        for area_id, area_name, search_text in targets:
            if len(all_jobs) >= max_jobs:
                break

            try:
                url = (
                    f"{config.HH_RU_API_URL}"
                    f"?text={urllib.request.quote(search_text)}"
                    f"&area={area_id}"
                    f"&per_page=100"
                    f"&search_field=name"
                    f"&order_by=publication_time"
                )
                res_text = self._fetch_url(
                    url, headers={"User-Agent": self._hhru_user_agent}, timeout=20
                )
                data = json.loads(res_text)

                items = data.get("items", [])
                logger.info(f"hh.ru [{area_name}/{search_text}]: {len(items)} results")

                for item in items:
                    if len(all_jobs) >= max_jobs:
                        break

                    job = self._parse_hhru_item(item, area_name)
                    if job and job["id"] not in seen_ids:
                        seen_ids.add(job["id"])
                        all_jobs.append(job)

                # Rate limit: 0.5s between requests
                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"hh.ru [{area_name}/{search_text}] error: {e}")
                continue

        logger.info(f"hh.ru total: {len(all_jobs)} unique jobs")
        return all_jobs[:max_jobs]

    # ══════════════════════════════════════════════════════════════════════
    # Indeed FREE RSS Feed (no blocks, no API key)
    # ══════════════════════════════════════════════════════════════════════

    def _parse_indeed_rss_item(self, item: ET.Element, default_loc: str) -> dict | None:
        """Parse a single indeed RSS item element."""
        title = ""
        company = ""
        link = ""
        loc = default_loc
        snippet = ""

        title_elem = item.find("title")
        if title_elem is not None and title_elem.text:
            title_text = title_elem.text.strip()
            # Indeed RSS format: "Job Title - Company Name"
            if " - " in title_text:
                parts = title_text.rsplit(" - ", 1)
                title = parts[0].strip()
                company = parts[1].strip()
            else:
                title = title_text

        link_elem = item.find("link")
        if link_elem is not None and link_elem.text:
            link = link_elem.text.strip()

        desc_elem = item.find("description")
        if desc_elem is not None and desc_elem.text:
            import re
            snippet = re.sub(r"<[^>]+>", "", desc_elem.text).strip()[:300]
            loc_match = re.search(r"Location[:\s]+([^\n<]+)", snippet, re.I)
            if loc_match:
                loc = loc_match.group(1).strip()

        if not title or not company:
            return None

        return {
            "title": title,
            "company": company,
            "url": link,
            "location": loc,
            "snippet": snippet,
        }

    def _fetch_and_parse_indeed_rss_country(
        self, country_key: str, search_query: str, indeed_loc: str, seen: set, max_jobs: int
    ) -> list[dict]:
        """Fetch and parse Indeed RSS feed for a single country location."""
        jobs = []
        try:
            from urllib.parse import urlencode
            params = {"q": search_query, "l": indeed_loc, "sort": "date"}
            url = f"{config.INDEED_RSS_URL}?{urlencode(params)}"

            xml_text = self._fetch_url(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; JobHuntBot/17.0)",
                    "Accept": "application/rss+xml, application/xml, text/xml",
                },
                timeout=20,
            )

            try:
                root = ET.fromstring(xml_text)
            except ET.ParseError:
                logger.warning(f"Indeed RSS [{country_key}]: XML parse error")
                return []

            for item in root.iter("item"):
                parsed = self._parse_indeed_rss_item(item, indeed_loc)
                if parsed:
                    title = parsed["title"]
                    company = parsed["company"]
                    key = (company.lower().strip(), title.lower().strip())
                    if key not in seen:
                        seen.add(key)
                        jobs.append(
                            {
                                "id": f"indeed_rss_{country_key}_{len(seen)}",
                                "title": title[:100],
                                "company": company[:80],
                                "location": parsed["location"][:60],
                                "source": "indeed_rss",
                                "url": parsed["url"],
                                "email": _clean_email(company, parsed["url"]),
                                "snippet": parsed["snippet"][:200],
                                "job_id": f"ir_{country_key}_{len(seen)}",
                            }
                        )
            logger.info(f"Indeed RSS [{country_key}]: {len(jobs)} jobs")
        except Exception as e:
            logger.warning(f"Indeed RSS [{country_key}] error: {e}")
        return jobs

    def search_indeed_rss(
        self, max_jobs: int = 50, query: str = "", location: str = ""
    ) -> list[dict]:
        """
        Search Indeed via FREE RSS feeds for all target countries.
        RSS feeds never return 403 — XML is publicly accessible.

        Rate limit: 1 request per 2s (polite to Indeed servers).
        """
        all_jobs = []
        seen = set()

        search_query = query or "network engineer"
        selected_keys = []
        custom_location = ""

        if location:
            loc_lower = location.lower()
            matched_key = None
            for k in INDEED_RSS_LOCATIONS:
                if k in loc_lower or loc_lower in k:
                    matched_key = k
                    break
            if matched_key:
                selected_keys = [matched_key]
            else:
                custom_location = location
        else:
            all_keys = list(INDEED_RSS_LOCATIONS.keys())
            rng = random.Random(int(time.time() // 300))
            rng.shuffle(all_keys)
            selected_keys = all_keys[:5]

        loops = selected_keys if not custom_location else [None]
        for country_key in loops:
            if len(all_jobs) >= max_jobs:
                break

            if custom_location:
                indeed_loc = custom_location
                country_key = "custom"
            else:
                indeed_loc = INDEED_RSS_LOCATIONS.get(country_key, "")

            country_jobs = self._fetch_and_parse_indeed_rss_country(
                country_key, search_query, indeed_loc, seen, max_jobs
            )
            all_jobs.extend(country_jobs)
            time.sleep(2)  # Rate limit: 2s between countries

        logger.info(f"Indeed RSS total: {len(all_jobs)} jobs")
        return all_jobs[:max_jobs]

    # ══════════════════════════════════════════════════════════════════════
    # Glassdoor Free Scraper (basic HTTP, best effort)
    # ══════════════════════════════════════════════════════════════════════

    def _parse_glassdoor_item(
        self,
        i: int,
        titles: list[str],
        companies: list[str],
        locations: list[str],
        links: list[str]
    ) -> dict | None:
        """Parse a single Glassdoor listing by indices."""
        import re
        title_text = re.sub(r"<[^>]+>", "", titles[i]).strip()
        company_text = re.sub(r"<[^>]+>", "", companies[i]).strip()
        loc_text = (
            re.sub(r"<[^>]+>", "", locations[i]).strip()
            if i < len(locations)
            else "Remote"
        )
        job_url = (
            f"{config.GLASSDOOR_BASE_URL}{links[i]}"
            if i < len(links)
            else ""
        )

        if not title_text or not company_text:
            return None

        return {
            "title": title_text,
            "company": company_text,
            "location": loc_text,
            "url": job_url,
        }

    def _fetch_and_parse_glassdoor_query(
        self, q_val: str, seen: set, max_jobs: int
    ) -> list[dict]:
        """Fetch and parse Glassdoor listings for a single search query."""
        jobs = []
        try:
            q_encoded = urllib.request.quote(q_val)
            url = f"{config.GLASSDOOR_BASE_URL}/Job/jobs.htm?sc.keyword={q_encoded}&locT=C&locId=0"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            html = self._fetch_url(url, headers=headers, timeout=15)
            if not html:
                return []

            # Parse with regex (Avoid heavy BeautifulSoup dependency in PA context)
            import re

            # Find job cards — Glassdoor uses various HTML patterns
            title_pattern = re.findall(
                r'class="[^"]*job-title[^"]*"[^>]*>(.*?)</a>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            company_pattern = re.findall(
                r'class="[^"]*(?:employer-name|company-name|job-employer)[^"]*"[^>]*>(.*?)</(?:span|div)>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            location_pattern = re.findall(
                r'class="[^"]*(?:location|job-location)[^"]*"[^>]*>(.*?)</(?:span|div)>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            link_pattern = re.findall(
                r'href="(/Job/[^"]+\.htm[^"]*)"', html, re.IGNORECASE
            )

            for i in range(min(len(title_pattern), len(company_pattern), 30)):
                if len(jobs) >= max_jobs:
                    break

                parsed = self._parse_glassdoor_item(
                    i, title_pattern, company_pattern, location_pattern, link_pattern
                )
                if parsed:
                    title_text = parsed["title"]
                    company_text = parsed["company"]
                    key = (company_text.lower().strip(), title_text.lower().strip())
                    if key not in seen:
                        seen.add(key)
                        jobs.append(
                            {
                                "id": f"gd_{len(seen)}",
                                "title": title_text[:100],
                                "company": company_text[:80],
                                "location": parsed["location"][:60],
                                "source": "glassdoor",
                                "url": parsed["url"],
                                "email": _clean_email(company_text, parsed["url"]),
                                "snippet": f"Glassdoor: {title_text} at {company_text}",
                                "job_id": f"gd_{len(seen)}",
                            }
                        )
            logger.info(f"Glassdoor [{q_val}]: {len(jobs)} jobs")
        except Exception as e:
            logger.warning(f"Glassdoor [{q_val}] error: {e}")
        return jobs

    def search_glassdoor(
        self, max_jobs: int = 30, query: str = "", location: str = ""
    ) -> list[dict]:
        """
        Scrape Glassdoor free job listings via basic HTTP requests.
        Glassdoor has aggressive anti-bot — best-effort.

        URL pattern: https://www.glassdoor.com/Job/jobs.htm?sc.keyword=NETWORK+ENGINEER
        """
        all_jobs = []
        seen = set()

        if query:
            selected_titles = [query]
        else:
            # Rotate 3 random titles + US/global location
            rng = random.Random(int(time.time() // 300))
            titles_pool = list(TITLES[:6])
            rng.shuffle(titles_pool)
            selected_titles = titles_pool[:3]

        for q_val in selected_titles:
            if len(all_jobs) >= max_jobs:
                break

            q_jobs = self._fetch_and_parse_glassdoor_query(q_val, seen, max_jobs)
            all_jobs.extend(q_jobs)
            time.sleep(3)  # Glassdoor is aggressive against bots

        logger.info(f"Glassdoor total: {len(all_jobs)} jobs")
        return all_jobs[:max_jobs]

    # ══════════════════════════════════════════════════════════════════════
    # LinkedIn XHR (free, no auth needed on PA)
    # ══════════════════════════════════════════════════════════════════════

    def search_linkedin_xhr(
        self, max_jobs: int = 50, query: str = "", location: str = ""
    ) -> list[dict]:
        """Search LinkedIn XHR API (works on PA, no auth needed)."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not available")
            return []

        all_jobs = []
        seen = set()

        if query or location:
            selected_titles = [query or "network engineer"]
            selected_countries = []
            custom_city = ""
            if location:
                loc_lower = location.lower()
                matched_key = None
                for k in CITIES:
                    if k in loc_lower or loc_lower in k:
                        matched_key = k
                        break
                if matched_key:
                    selected_countries = [matched_key]
                else:
                    custom_city = location
            else:
                selected_countries = ["uae"]  # Default
        else:
            # Rotate: 3 random countries, 2 random titles per tick
            selected_countries, selected_titles = _get_rotation_selection(3, 2)

        for title in selected_titles:
            if len(all_jobs) >= max_jobs:
                break
            loops = selected_countries if not custom_city else [None]
            for country_key in loops:
                if len(all_jobs) >= max_jobs:
                    break
                city = custom_city if custom_city else CITIES.get(country_key, "")
                if not city:
                    continue

                try:
                    url = (
                        f"{config.LINKEDIN_JOBS_API_URL}"
                        f"?keywords={urllib.request.quote(title)}"
                        f"&location={urllib.request.quote(city)}&start=0&count=10"
                    )
                    html_text = self._fetch_url(url)
                    if not html_text:
                        continue
                    soup = BeautifulSoup(html_text, "html.parser")
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
                            all_jobs.append(
                                {
                                    "id": f"li_{len(all_jobs)}",
                                    "title": t[:100],
                                    "company": comp[:80],
                                    "location": str(loc or city)[:60],
                                    "source": "linkedin_xhr",
                                    "url": href,
                                    "email": _clean_email(comp, href),
                                    "snippet": "",
                                }
                            )
                except Exception as e:
                    logger.debug(f"LinkedIn XHR [{title}/{city}] error: {e}")

        logger.info(f"LinkedIn XHR total: {len(all_jobs)} jobs")
        return all_jobs[:max_jobs]

    # ══════════════════════════════════════════════════════════════════════
    # Unified search_all() — GLOBAL SCALE with rotation
    # ══════════════════════════════════════════════════════════════════════

    def _add_scraped_jobs(
        self,
        jobs: list[dict],
        all_jobs: list[dict],
        seen_keys: set,
        seen_urls: set,
        label: str
    ) -> int:
        """Helper to deduplicate and add jobs to search list."""
        added = 0
        for j in jobs:
            key = (
                j.get("company", "").lower().strip(),
                j.get("title", "").lower().strip(),
            )
            url = (
                (j.get("url", "") or "").split("?")[0].rstrip("/")
            )  # canonical URL
            if key in seen_keys:
                continue
            if url and url in seen_urls:
                continue
            seen_keys.add(key)
            if url:
                seen_urls.add(url)
            all_jobs.append(j)
            added += 1
        logger.info(f"  [{label}] +{added} jobs (total: {len(all_jobs)})")
        return added

    def _check_scraped_cache(self, query: str, max_jobs: int) -> tuple[bool, list[dict]]:
        """Check cache first. Return (cache_hit, jobs)."""
        cached_ts, cached_jobs = _load_cache()
        if query:
            matching_cached = [
                j
                for j in cached_jobs
                if query.lower() in j.get("title", "").lower()
                or query.lower() in j.get("snippet", "").lower()
                or query.lower() in j.get("company", "").lower()
            ]
            if len(matching_cached) >= 10 and (time.time() - cached_ts) < _CACHE_TTL:
                logger.info(
                    f"📦 Cache hit for query '{query}': {len(matching_cached)} matching jobs"
                )
                return True, matching_cached[:max_jobs]
            else:
                logger.info(
                    f"Cache miss or insufficient matches for query '{query}' — scraping fresh"
                )
        else:
            if cached_jobs and (time.time() - cached_ts) < _CACHE_TTL:
                logger.info(
                    f"📦 Cache hit: {len(cached_jobs)} jobs, {int(time.time() - cached_ts)}s old"
                )
                return True, cached_jobs[:max_jobs]
        return False, []

    def _run_free_scrapers(
        self, query: str, location: str, max_jobs: int, seen_keys: set, seen_urls: set
    ) -> list[dict]:
        """Run all healthy free scrapers concurrently."""
        all_jobs = []
        from concurrent.futures import ThreadPoolExecutor, as_completed

        free_scrapers_all = {
            "Remotive": (
                "remotive",
                lambda: self.search_remotive(max_jobs=25, query=query),
            ),
            "Arbeitnow": (
                "arbeitnow",
                lambda: self.search_arbeitnow(max_jobs=25, query=query),
            ),
            "RemoteOK": (
                "remoteok",
                lambda: self.search_remoteok(max_jobs=25, query=query),
            ),
            "WeWorkRemotely": (
                "weworkremotely",
                lambda: self.search_weworkremotely(max_jobs=25, query=query),
            ),
            "TheMuse": (
                "themuse",
                lambda: self.search_themuse(max_jobs=25, query=query),
            ),
            "Jobicy": ("jobicy", lambda: self.search_jobicy(max_jobs=25, query=query)),
            "hhru": (
                "hhru",
                lambda: self.search_hhru(max_jobs=80, query=query, location=location),
            ),
            "IndeedRSS": (
                "indeed_rss",
                lambda: self.search_indeed_rss(
                    max_jobs=50, query=query, location=location
                ),
            ),
            "Glassdoor": (
                "glassdoor",
                lambda: self.search_glassdoor(
                    max_jobs=30, query=query, location=location
                ),
            ),
            "LinkedInXHR": (
                "linkedin_xhr",
                lambda: self.search_linkedin_xhr(
                    max_jobs=50, query=query, location=location
                ),
            ),
        }

        # Skip sources currently in circuit-breaker cooldown
        free_scrapers = {
            label: func
            for label, (cb_key, func) in free_scrapers_all.items()
            if _source_is_healthy(cb_key)
        }
        skipped = set(free_scrapers_all) - set(free_scrapers)
        if skipped:
            logger.info(f"[Circuit] Skipping unhealthy sources: {', '.join(skipped)}")

        with ThreadPoolExecutor(max_workers=min(len(free_scrapers), 10)) as executor:
            future_to_info = {
                executor.submit(func): (label, free_scrapers_all[label][0])
                for label, func in free_scrapers.items()
            }
            for future in as_completed(future_to_info):
                label, cb_key = future_to_info[future]
                try:
                    jobs = future.result()
                    self._add_scraped_jobs(jobs, all_jobs, seen_keys, seen_urls, label)
                    _record_source_success(cb_key)
                except Exception as e:
                    logger.warning(f"{label} search failed: {e}")
                    _record_source_failure(cb_key)
        return all_jobs

    def _run_jsearch_fallback(
        self, query: str, location: str, max_jobs: int, seen_keys: set, seen_urls: set, all_jobs: list[dict]
    ) -> None:
        """Run JSearch API query as a fallback when free scrapers returned insufficient jobs."""
        logger.info(
            "=== PAJobScraper v4 GLOBAL: Phase 2 — JSearch API Fallback ==="
        )
        try:
            jsearch_jobs = self.search_jsearch(
                max_total=max_jobs, query=query, location=location
            )
            self._add_scraped_jobs(jsearch_jobs, all_jobs, seen_keys, seen_urls, "JSearch")
            _record_source_success("jsearch")
        except Exception as e:
            logger.warning(f"JSearch fallback failed: {e}")
            _record_source_failure("jsearch")

    def search_all(
        self, query: str = "", location: str = "", max_jobs: int = 150
    ) -> list[dict]:
        """
        GLOBAL SCALE job search — 8 sources, zero API keys needed for 7.

        Priority:
        1. Cache (2h TTL) — instant if fresh
        2. JSearch API (3 queries only — conserve 300/month quota)
        3. Remotive FREE API (worldwide remote — no key)
        4. Arbeitnow FREE API (Europe — no key)
        5. hh.ru FREE API (Russia/CIS — unlimited, no key)
        6. Indeed RSS (FREE XML — no blocks, unlimited)
        7. Glassdoor (FREE — best effort)
        8. LinkedIn XHR (free, no auth)

        Early-exit at 15 jobs. Rotation: 3 locations x 2 titles per tick.
        """
        hit, jobs = self._check_scraped_cache(query, max_jobs)
        if hit:
            return jobs

        seen_keys: set = set()  # (company, title) dedup
        seen_urls: set = set()  # URL-based dedup

        # Phase 1: Free sources run concurrently via ThreadPoolExecutor
        logger.info(
            "=== PAJobScraper v4 GLOBAL: Phase 1 — Concurrent Free Scrapers ==="
        )
        all_jobs = self._run_free_scrapers(query, location, max_jobs, seen_keys, seen_urls)

        # Phase 2: Fallback to JSearch API only if free sources did not yield enough jobs (conserve quota)
        if len(all_jobs) < 15:
            self._run_jsearch_fallback(query, location, max_jobs, seen_keys, seen_urls, all_jobs)
        else:
            logger.info(
                f"=== PAJobScraper v4: Skipping JSearch ({len(all_jobs)} jobs from free sources) ==="
            )

        # Save to cache
        if all_jobs:
            _save_cache(all_jobs)
            logger.info(f"💾 Cache saved: {len(all_jobs)} jobs")

        logger.info(
            f"PAJobScraper v3 GLOBAL: total {len(all_jobs)} jobs from 7 sources"
        )
        return all_jobs[:max_jobs]

    # ══════════════════════════════════════════════════════════════════════
    # NEW FREE SOURCES (2026-06-24 Deep Scan — zero API key needed)
    # ══════════════════════════════════════════════════════════════════════

    def search_remotive(self, max_jobs: int = 30, query: str = "") -> list[dict]:
        """Remotive public API — worldwide remote jobs, no key."""
        import json as _json

        try:
            search_query = query or "network engineer"
            url = f"{config.REMOTIVE_API_URL}?search={urllib.request.quote(search_query)}&limit=30"
            res_text = self._fetch_url(
                url,
                headers={"User-Agent": "JobHuntPro/17.0", "Accept": "application/json"},
                timeout=15,
            )
            data = _json.loads(res_text)
            jobs = []
            for j in data.get("jobs", []):
                title = j.get("title", "")
                company = j.get("company_name", "")
                if not title or not company:
                    continue
                from bs4 import BeautifulSoup

                desc = BeautifulSoup(
                    j.get("description", ""), "html.parser"
                ).get_text()[:300]
                jobs.append(
                    {
                        "id": f"remotive_{j.get('id', '')}",
                        "title": title[:100],
                        "company": company[:80],
                        "location": j.get("candidate_required_location", "Remote")[:60],
                        "source": "remotive",
                        "url": j.get("url", ""),
                        "email": _clean_email(company, j.get("url", "")),
                        "snippet": desc[:200],
                        "salary": j.get("salary", ""),
                        "job_id": f"rm_{j.get('id', '')}",
                    }
                )
            logger.info(f"Remotive: {len(jobs)} jobs")
            return jobs[:max_jobs]
        except Exception as e:
            logger.warning(f"Remotive search error: {e}")
            return []

    def search_arbeitnow(self, max_jobs: int = 30, query: str = "") -> list[dict]:
        """Arbeitnow public API — Europe/Germany jobs, no key."""
        import json as _json

        try:
            url = config.ARBEITNOW_API_URL
            res_text = self._fetch_url(
                url,
                headers={"User-Agent": "JobHuntPro/17.0", "Accept": "application/json"},
                timeout=15,
            )
            data = _json.loads(res_text)
            jobs = []
            from bs4 import BeautifulSoup

            for j in data.get("data", []):
                title = j.get("title", "")
                company = j.get("company_name", "")
                if not title or not company:
                    continue
                # Filter: match query or default network keywords
                tl = title.lower()
                desc_text = (
                    BeautifulSoup(j.get("description", ""), "html.parser")
                    .get_text()
                    .lower()
                )
                if query:
                    ql = query.lower()
                    if ql not in tl and ql not in desc_text:
                        continue
                else:
                    if not any(
                        kw in tl
                        for kw in [
                            "network",
                            "infrastructure",
                            "system",
                            "devops",
                            "security",
                            "cisco",
                            "cloud",
                            "sysadmin",
                            "administrator",
                            "engineer",
                        ]
                    ):
                        continue
                desc = BeautifulSoup(
                    j.get("description", ""), "html.parser"
                ).get_text()[:300]
                slug = j.get("slug", "")
                jobs.append(
                    {
                        "id": f"arbeitnow_{slug}",
                        "title": title[:100],
                        "company": company[:80],
                        "location": "Germany/Europe",
                        "source": "arbeitnow",
                        "url": f"{config.ARBEITNOW_VIEW_BASE_URL}/{slug}" if slug else "",
                        "email": _clean_email(company, j.get("url", "")),
                        "snippet": desc[:200],
                        "job_id": f"an_{slug}",
                    }
                )
            logger.info(f"Arbeitnow: {len(jobs)} jobs")
            return jobs[:max_jobs]
        except Exception as e:
            logger.warning(f"Arbeitnow search error: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # RemoteOK FREE API (worldwide remote — no key)
    # ══════════════════════════════════════════════════════════════════════

    def search_remoteok(self, max_jobs: int = 30, query: str = "") -> list[dict]:
        """RemoteOK public JSON API — zero cost, no key, great for remote IT roles."""
        try:
            url = config.REMOTEOK_API_URL
            res_text = self._fetch_url(
                url,
                headers={
                    "User-Agent": "JobHuntPro/18.0 (samsalameh.cv@gmail.com)",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            data = json.loads(res_text)
            # First element is a legal notice dict — skip it
            jobs = []
            kw = (query or "network engineer").lower().split()
            for item in data:
                if not isinstance(item, dict) or not item.get("position"):
                    continue
                title = (item.get("position") or "").strip()
                company = (item.get("company") or "").strip()
                if not title or not company:
                    continue
                # Relevance filter
                tl = title.lower()
                tags = " ".join(item.get("tags") or []).lower()
                if query and not any(k in tl or k in tags for k in kw):
                    continue
                job_url = (
                    item.get("url")
                    or f"{config.REMOTEOK_VIEW_BASE_URL}/{item.get('id', '')}"
                )
                desc = (item.get("description") or "")[:300]
                # Strip HTML tags
                import re as _re

                desc = _re.sub(r"<[^>]+>", "", desc).strip()
                jobs.append(
                    {
                        "id": f"rok_{item.get('id', len(jobs))}",
                        "title": title[:100],
                        "company": company[:80],
                        "location": "Remote",
                        "source": "remoteok",
                        "url": job_url,
                        "email": _clean_email(company, job_url),
                        "snippet": desc[:200],
                        "salary": item.get("salary") or "",
                        "job_id": f"rok_{item.get('id', '')}",
                    }
                )
                if len(jobs) >= max_jobs:
                    break
            logger.info(f"RemoteOK: {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.warning(f"RemoteOK search error: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # WeWorkRemotely RSS (free, zero auth)
    # ══════════════════════════════════════════════════════════════════════

    def search_weworkremotely(self, max_jobs: int = 30, query: str = "") -> list[dict]:
        """WeWorkRemotely public RSS feed — free, reliable, worldwide remote jobs."""
        try:
            feeds = [
                config.WEWORKREMOTELY_DEV_RSS,
                config.WEWORKREMOTELY_PROG_RSS,
            ]
            all_jobs: list[dict] = []
            seen: set = set()
            kw = (query or "network engineer").lower().split()
            import re as _re

            for feed_url in feeds:
                if len(all_jobs) >= max_jobs:
                    break
                try:
                    xml_text = self._fetch_url(
                        feed_url,
                        headers={
                            "User-Agent": "JobHuntPro/18.0",
                            "Accept": "application/rss+xml",
                        },
                        timeout=15,
                    )
                    root = ET.fromstring(xml_text)
                    for item in root.iter("item"):
                        t_el = item.find("title")
                        l_el = item.find("link")
                        d_el = item.find("description")
                        if t_el is None or not t_el.text:
                            continue
                        raw_title = t_el.text.strip()
                        # WWR format: "Company: Job Title"
                        if ": " in raw_title:
                            company, title = raw_title.split(": ", 1)
                        else:
                            company, title = "", raw_title
                        company = company.strip()
                        title = title.strip()
                        if not title:
                            continue
                        tl = title.lower()
                        if query and not any(k in tl for k in kw):
                            continue
                        link = (l_el.text or "").strip() if l_el is not None else ""
                        key = (company.lower(), title.lower())
                        if key in seen:
                            continue
                        seen.add(key)
                        desc = ""
                        if d_el is not None and d_el.text:
                            desc = _re.sub(r"<[^>]+>", "", d_el.text).strip()[:200]
                        all_jobs.append(
                            {
                                "id": f"wwr_{len(all_jobs)}",
                                "title": title[:100],
                                "company": company[:80],
                                "location": "Remote",
                                "source": "weworkremotely",
                                "url": link,
                                "email": _clean_email(company, link),
                                "snippet": desc,
                                "job_id": f"wwr_{len(all_jobs)}",
                            }
                        )
                        if len(all_jobs) >= max_jobs:
                            break
                    time.sleep(1)
                except Exception as fe:
                    logger.debug(f"WWR feed {feed_url} error: {fe}")
            logger.info(f"WeWorkRemotely: {len(all_jobs)} jobs")
            return all_jobs[:max_jobs]
        except Exception as e:
            logger.warning(f"WeWorkRemotely search error: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # The Muse FREE API (global companies — no key needed for public data)
    # ══════════════════════════════════════════════════════════════════════

    def search_themuse(self, max_jobs: int = 25, query: str = "") -> list[dict]:
        """The Muse public jobs API — worldwide companies, no API key needed."""
        try:
            search_q = query or "network engineer"
            url = f"{config.THEMUSE_API_URL}?query={urllib.request.quote(search_q)}&page=1&descending=true"
            res_text = self._fetch_url(
                url,
                headers={
                    "User-Agent": "JobHuntPro/18.0",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            data = json.loads(res_text)
            jobs = []
            for item in data.get("results", []):
                title = (item.get("name") or "").strip()
                co_data = item.get("company") or {}
                company = (
                    co_data.get("name") if isinstance(co_data, dict) else str(co_data)
                ).strip()
                if not title or not company:
                    continue
                locs = item.get("locations") or []
                loc_str = (
                    ", ".join(l.get("name", "") for l in locs if isinstance(l, dict))[
                        :60
                    ]
                    or "Remote"
                )
                refs = item.get("refs") or {}
                job_url = refs.get("landing_page") or ""
                jobs.append(
                    {
                        "id": f"muse_{item.get('id', len(jobs))}",
                        "title": title[:100],
                        "company": company[:80],
                        "location": loc_str,
                        "source": "themuse",
                        "url": job_url,
                        "email": _clean_email(company, job_url),
                        "snippet": "",
                        "job_id": f"muse_{item.get('id', '')}",
                    }
                )
                if len(jobs) >= max_jobs:
                    break
            logger.info(f"The Muse: {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.warning(f"The Muse search error: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # Jobicy FREE API (remote-first, worldwide — no key)
    # ══════════════════════════════════════════════════════════════════════

    def search_jobicy(self, max_jobs: int = 25, query: str = "") -> list[dict]:
        """Jobicy public JSON API — remote tech jobs, zero cost, no key."""
        try:
            url = f"{config.JOBICY_API_URL}?count=50&industrySlug=it"
            if query:
                url += f"&tag={urllib.request.quote(query.replace(' ', '-'))}"
            res_text = self._fetch_url(
                url,
                headers={
                    "User-Agent": "JobHuntPro/18.0",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            data = json.loads(res_text)
            jobs = []
            kw = (query or "").lower().split()
            for item in data.get("jobs", []):
                title = (item.get("jobTitle") or "").strip()
                company = (item.get("companyName") or "").strip()
                if not title or not company:
                    continue
                tl = title.lower()
                if kw and not any(k in tl for k in kw):
                    continue
                job_url = item.get("url") or ""
                snippet = (item.get("jobExcerpt") or "")[:200]
                jobs.append(
                    {
                        "id": f"jcy_{item.get('id', len(jobs))}",
                        "title": title[:100],
                        "company": company[:80],
                        "location": (item.get("jobGeo") or "Remote")[:60],
                        "source": "jobicy",
                        "url": job_url,
                        "email": _clean_email(company, job_url),
                        "snippet": snippet,
                        "salary": item.get("annualSalaryMin")
                        and f"${item['annualSalaryMin']}-${item.get('annualSalaryMax', '?')}"
                        or "",
                        "job_id": f"jcy_{item.get('id', '')}",
                    }
                )
                if len(jobs) >= max_jobs:
                    break
            logger.info(f"Jobicy: {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.warning(f"Jobicy search error: {e}")
            return []

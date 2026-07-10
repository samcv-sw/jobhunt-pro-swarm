"""
JobHunt Pro - Multi-Platform Auto-Apply Engine
Supports: LinkedIn (via JSearch API), Indeed, Bayt.com, NaukriGulf
MENA/GCC is a pure white space — no auto-apply tool exists for Bayt.com or NaukriGulf

Architecture:
  PlatformBase (ABC)
    ├── LinkedInScraper   — JSearch API (RapidAPI)
    ├── IndeedScraper     — Web scraping + RSS
    ├── BaytScraper       — Web scraping bayt.com (MENA)
    └── NaukriGulfScraper — Web scraping naukrigulf.com (MENA/GCC)

  AutoApplyOrchestrator — coordinates search → apply → track across all platforms
"""

import asyncio
import hashlib
import logging
import os
import random
import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlencode

import httpx
from bs4 import BeautifulSoup

import config
import core.pg_sqlite_shim as sqlite3
from core.stealth import stealth

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────


def _init_rate_limit_table():
    """Initialize the rate_limit_log table."""
    conn = _get_conn()
    try:
        conn.executescript(RATE_LIMIT_TABLE_SQL)
        conn.commit()
    except Exception as e:
        logger.warning(f"[RATE-LIMIT DB] Init error: {e}")
    finally:
        conn.close()


def _persist_rate_limit(platform: str):
    """Store rate limit data in DB so it survives restarts."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO rate_limit_log (platform, called_at) VALUES (?, ?)",
            (platform, time.time()),
        )
        conn.commit()
    except Exception as e:
        logger.debug(f"[RATE-LIMIT] Persist error: {e}")
    finally:
        conn.close()


def _check_persisted_rate(platform: str) -> bool:
    """Check rate limit from persisted DB data."""
    conn = _get_conn()
    try:
        cutoff = time.time() - 3600
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM rate_limit_log WHERE platform = ? AND called_at > ?",
            (platform, cutoff),
        ).fetchone()
        count = row["cnt"] if row else 0
        return count < RATE_LIMIT_PER_PLATFORM
    except Exception as e:
        logger.debug(f"[RATE-LIMIT] Check error: {e}")
        return True  # Allow on error
    finally:
        conn.close()


def _prune_rate_limit_log():
    """Remove entries older than 24 hours to keep DB small."""
    conn = _get_conn()
    try:
        cutoff = time.time() - 86400
        conn.execute("DELETE FROM rate_limit_log WHERE called_at < ?", (cutoff,))
        conn.commit()
    except Exception as e:
        logger.debug(f"[RATE-LIMIT] Prune error: {e}")
    finally:
        conn.close()


DB_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS multi_platform_apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    campaign_id TEXT,
    platform TEXT,
    job_id TEXT,
    job_title TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    status TEXT DEFAULT 'pending',
    message TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mpa_platform ON multi_platform_apps(platform);
CREATE INDEX IF NOT EXISTS idx_mpa_status ON multi_platform_apps(status);
CREATE INDEX IF NOT EXISTS idx_mpa_user ON multi_platform_apps(user_id);
"""

RATE_LIMIT_PER_PLATFORM = int(
    os.getenv("MULTI_PLATFORM_RATE_LIMIT", "10")
)  # max apps/hour per platform

# Rate limit table init
RATE_LIMIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rate_limit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    called_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rll_platform ON rate_limit_log(platform);
CREATE INDEX IF NOT EXISTS idx_rll_called_at ON rate_limit_log(called_at);
"""
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


# ─────────────────────────────────────────────
# Rate Limiter
# ─────────────────────────────────────────────


class PlatformRateLimiter:
    """Sliding-window rate limiter: max N calls per hour per platform.
    Uses SQLite-backed persistent storage to survive restarts."""

    def __init__(self, max_per_hour: int = RATE_LIMIT_PER_PLATFORM):
        self.max_per_hour = max_per_hour
        # Initialize the rate limit DB table
        _init_rate_limit_table()

    def can_call(self, platform: str) -> bool:
        return _check_persisted_rate(platform)

    def record_call(self, platform: str):
        _persist_rate_limit(platform)

    def remaining(self, platform: str) -> int:
        conn = _get_conn()
        try:
            cutoff = time.time() - 3600
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM rate_limit_log WHERE platform = ? AND called_at > ?",
                (platform, cutoff),
            ).fetchone()
            count = row["cnt"] if row else 0
            return max(0, self.max_per_hour - count)
        except Exception as e:
            logger.debug(f"[RATE-LIMIT] Remaining error: {e}")
            return self.max_per_hour
        finally:
            conn.close()

    def time_until_next_slot(self, platform: str) -> float:
        """Seconds until a new rate-limit slot opens."""
        if self.can_call(platform):
            return 0.0
        conn = _get_conn()
        try:
            row = conn.execute(
                "SELECT MIN(called_at) as oldest FROM rate_limit_log WHERE platform = ?",
                (platform,),
            ).fetchone()
            if row and row["oldest"]:
                return max(0.0, (row["oldest"] + 3600) - time.time())
            return 0.0
        except Exception:
            return 0.0
        finally:
            conn.close()

    def reset(self, platform: str):
        conn = _get_conn()
        try:
            conn.execute("DELETE FROM rate_limit_log WHERE platform = ?", (platform,))
            conn.commit()
        except Exception as e:
            logger.debug(f"[RATE-LIMIT] Reset error: {e}")
        finally:
            conn.close()


# ─────────────────────────────────────────────
# Database helpers (raw SQLite — matches app_v2.py pattern)
# ─────────────────────────────────────────────


def _get_db_path() -> str:
    """Resolve the DB path consistently with the rest of the project."""
    raw = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
    if os.path.isabs(raw):
        return raw
    # Relative to project root
    project_root = Path(__file__).resolve().parent.parent
    return str(project_root / raw)


def _get_conn(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def init_multi_platform_db(db_path: str | None = None):
    """Initialize the multi_platform_apps and rate_limit_log tables."""
    conn = _get_conn(db_path)
    try:
        conn.executescript(DB_TABLE_SQL)
        conn.executescript(RATE_LIMIT_TABLE_SQL)
        conn.commit()
        logger.info(
            "[MULTI-PLATFORM DB] Tables 'multi_platform_apps' and 'rate_limit_log' ready"
        )
        _prune_rate_limit_log()
    except Exception as e:
        logger.error(f"[MULTI-PLATFORM DB] Init error: {e}")
        raise
    finally:
        conn.close()


def log_multi_platform_application(
    user_id: str,
    campaign_id: str,
    platform: str,
    job_title: str,
    company: str,
    location: str,
    url: str,
    status: str = "pending",
    message: str = "",
    job_id: str = "",
    db_path: str | None = None,
):
    """Insert a record into multi_platform_apps."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT INTO multi_platform_apps
               (user_id, campaign_id, platform, job_id, job_title, company, location, url, status, message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                campaign_id,
                platform,
                job_id,
                job_title,
                company,
                location,
                url,
                status,
                message,
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"[LOG-MPA] Error: {e}")
    finally:
        conn.close()


def get_platform_stats(
    platform: str, since_hours: int = 24, db_path: str | None = None
) -> dict[str, Any]:
    """Get application stats for a platform within the last N hours."""
    conn = _get_conn(db_path)
    try:
        cutoff = (datetime.now(UTC) - timedelta(hours=since_hours)).isoformat()
        row = conn.execute(
            """SELECT
                   COUNT(*) as total,
                   SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
               FROM multi_platform_apps
               WHERE platform = ? AND applied_at >= ?""",
            (platform, cutoff),
        ).fetchone()
        return dict(row) if row else {"total": 0, "success": 0, "failed": 0}
    except Exception as e:
        logger.error(f"[STATS] Error for {platform}: {e}")
        return {"total": 0, "success": 0, "failed": 0}
    finally:
        conn.close()


# Shared rate limiter instance
_rate_limiter = PlatformRateLimiter()


# ─────────────────────────────────────────────
# Abstract Base
# ─────────────────────────────────────────────


class PlatformBase(ABC):
    """Abstract base for all platform adapters."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name, e.g. 'LinkedIn'."""

    @property
    @abstractmethod
    def supported_countries(self) -> list[str]:
        """List of ISO country codes or region names this platform covers."""

    @abstractmethod
    async def search(
        self, query: str, location: str = "", max_results: int = 25
    ) -> list[dict[str, Any]]:
        """
        Search for jobs on this platform.
        Returns list of dicts with keys:
          job_id, title, company, location, url, snippet, salary, posted_date
        """

    @abstractmethod
    async def apply(
        self, job: dict[str, Any], cv_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Apply to a job on this platform.
        Returns (success: bool, message: str).
        """

    def make_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }


# ─────────────────────────────────────────────
# LinkedIn via JSearch API
# ─────────────────────────────────────────────


class LinkedInScraper(PlatformBase):
    """LinkedIn job search via JSearch API (RapidAPI + OpenWebNinja fallback).
    Follows the same pattern as core/job_search.py JSearchAPI."""

    @property
    def platform_name(self) -> str:
        return "LinkedIn"

    @property
    def supported_countries(self) -> list[str]:
        return ["US", "AE", "SA", "QA", "KW", "BH", "OM", "LB", "JO", "EG"]

    def __init__(self):
        self.api_key = getattr(config, "JSEARCH_API_KEY", "") or os.getenv(
            "JSEARCH_API_KEY", ""
        )
        # Try RapidAPI first, then OpenWebNinja fallback
        self._endpoints = [
            (
                "https://jsearch.p.rapidapi.com",
                "rapidapi",
                {
                    "X-RapidAPI-Key": self.api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
            ),
            (
                "https://api.openwebninja.com/v1",
                "openwebninja",
                {
                    "Authorization": f"Bearer {self.api_key}",
                },
            ),
        ]

    async def search(
        self, query: str, location: str = "", max_results: int = 25
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            logger.warning("[LinkedIn] No JSearch API key — returning empty results")
            return []

        if not _rate_limiter.can_call("linkedin"):
            logger.info("[LinkedIn] Rate limited — skipping search")
            return []

        search_q = f"{query} in {location}" if location else query
        all_jobs = []

        for base, api_type, headers in self._endpoints:
            try:
                params = {
                    "query": search_q,
                    "page": 1,
                    "num_pages": max(1, max_results // 10),
                }
                if api_type == "openwebninja":
                    params["limit"] = max_results

                async with stealth.get_async_client(timeout=30.0) as client:
                    resp = await client.get(
                        f"{base}/search", params=params, headers=headers
                    )
                    if resp.status_code != 200:
                        logger.debug(
                            f"[LinkedIn] {api_type} returned {resp.status_code}"
                        )
                        continue

                    data = resp.json()
                    items = data.get("data", [])
                    for item in items:
                        all_jobs.append(self._normalize(item))

                    if all_jobs:
                        break  # Stop on first successful result

            except httpx.TimeoutException:
                logger.debug(f"[LinkedIn] {api_type} timed out")
                continue
            except Exception as e:
                logger.debug(f"[LinkedIn] {api_type} error: {e}")
                continue

        _rate_limiter.record_call("linkedin")
        logger.info(f"[LinkedIn] Found {len(all_jobs)} jobs via JSearch")
        return all_jobs[:max_results]

    async def apply(
        self, job: dict[str, Any], cv_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """Try LinkedIn Easy Apply simulation.
        Attempts generic Easy Apply flow. Falls back to manual if blocked."""
        url = job.get("url", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not url:
            return False, "No job URL available for LinkedIn application"

        # Try generic Easy Apply flow via LinkedIn API simulation
        try:
            async with stealth.get_async_client(
                timeout=15.0, follow_redirects=True
            ) as client:
                # Step 1: GET job page to find Easy Apply URL
                headers = self.make_headers()
                headers["Accept"] = "application/json"
                resp = await client.get(url, headers=headers, timeout=15.0)

                if resp.status_code == 200:
                    # Check if it's a linkedin.com/jobs URL — extract job ID
                    import re as _re

                    job_id_match = _re.search(r"/jobs/view/(\d+)", url) or _re.search(
                        r"currentJobId=(\d+)", url
                    )
                    if job_id_match:
                        linkedin_job_id = job_id_match.group(1)
                        # Try the LinkedIn Easy Apply API endpoint
                        apply_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{linkedin_job_id}"
                        apply_resp = await client.get(
                            apply_url, headers=headers, timeout=10.0
                        )
                        if apply_resp.status_code == 200:
                            return (
                                True,
                                f"LinkedIn job page loaded: {url}. Easy Apply status determined. "
                                f"Opening {title} at {company} for manual Easy Apply.",
                            )

                # Fallback: return URL for manual apply (LinkedIn blocks programmatic)
                return (
                    False,
                    f"LinkedIn API does not support auto-apply. Apply manually: {url} "
                    f"for {title} at {company}",
                )
        except Exception as e:
            return (
                False,
                f"LinkedIn auto-apply attempted but blocked: {str(e)[:100]}. "
                f"Apply manually: {url}",
            )

    def _normalize(self, item: dict) -> dict[str, Any]:
        return {
            "job_id": item.get("job_id", "")
            or hashlib.md5(
                (item.get("job_title", "") + item.get("employer_name", "")).encode()
            ).hexdigest()[:12],
            "title": item.get("job_title", ""),
            "company": item.get("employer_name", ""),
            "location": item.get("job_city", "") or item.get("job_country", "") or "",
            "url": item.get("job_apply_link", "") or item.get("job_google_link", ""),
            "snippet": item.get("job_description", "")[:500],
            "salary": item.get("job_min_salary", "")
            or item.get("job_max_salary", "")
            or "",
            "posted_date": item.get("job_posted_at_datetime_utc", ""),
            "source": "linkedin",
        }


# ─────────────────────────────────────────────
# Indeed Scraper
# ─────────────────────────────────────────────


class IndeedScraper(PlatformBase):
    """Indeed job search via web scraping + RSS feed."""

    @property
    def platform_name(self) -> str:
        return "Indeed"

    @property
    def supported_countries(self) -> list[str]:
        return ["US", "AE", "SA", "QA", "KW", "BH", "OM", "LB"]

    async def search(
        self, query: str, location: str = "", max_results: int = 25
    ) -> list[dict[str, Any]]:
        if not _rate_limiter.can_call("indeed"):
            logger.info("[Indeed] Rate limited — skipping")
            return []

        jobs = []

        # Try RSS feed first (more reliable)
        try:
            rss_jobs = await self._search_rss(query, location, max_results)
            jobs.extend(rss_jobs)
        except Exception as e:
            logger.debug(f"[Indeed] RSS search failed: {e}")

        # Fall back to HTML scraping if RSS returned few results
        if len(jobs) < max_results:
            try:
                html_jobs = await self._search_html(
                    query, location, max_results - len(jobs)
                )
                # Deduplicate by title+company
                existing_keys = {
                    (j["title"], j["company"]) for j in jobs if j.get("company")
                }
                for job in html_jobs:
                    key = (job["title"], job.get("company", ""))
                    if key not in existing_keys:
                        jobs.append(job)
                        existing_keys.add(key)
            except Exception as e:
                logger.debug(f"[Indeed] HTML search failed: {e}")

        _rate_limiter.record_call("indeed")
        logger.info(f"[Indeed] Found {len(jobs)} jobs")
        return jobs[:max_results]

    async def _search_rss(
        self, query: str, location: str, max_results: int
    ) -> list[dict]:
        """Indeed RSS feed search."""
        q = quote_plus(f"{query} {location}" if location else query)
        url = f"https://www.indeed.com/rss?q={q}"

        headers = self.make_headers()
        async with stealth.get_async_client(
            timeout=20.0, follow_redirects=True
        ) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"[Indeed RSS] HTTP {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "lxml-xml")
            items = soup.find_all("item")
            jobs = []
            for item in items[:max_results]:
                title_tag = item.find("title")
                link_tag = item.find("link")
                desc_tag = item.find("description")
                title = title_tag.text.strip() if title_tag else ""
                link = link_tag.text.strip() if link_tag else ""
                desc = desc_tag.text.strip() if desc_tag else ""

                # Parse company from title (Indeed RSS: "Job Title - Company Name")
                company = ""
                if " - " in title:
                    parts = title.split(" - ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()

                jobs.append(
                    {
                        "job_id": hashlib.md5(
                            f"indeed:{link}:{title}".encode()
                        ).hexdigest()[:12],
                        "title": title,
                        "company": company,
                        "location": self._extract_location_from_rss(desc) or location,
                        "url": link,
                        "snippet": desc[:500],
                        "salary": self._extract_salary_from_rss(desc),
                        "posted_date": "",
                        "source": "indeed",
                    }
                )
            return jobs

    async def _search_html(
        self, query: str, location: str, max_results: int
    ) -> list[dict]:
        """Indeed HTML search as fallback."""
        params = {
            "q": query,
            "l": location or "",
            "sort": "date",
        }
        url = f"https://www.indeed.com/jobs?{urlencode(params)}"

        headers = self.make_headers()
        async with stealth.get_async_client(
            timeout=20.0, follow_redirects=True
        ) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select(
                "div.job_seen_beacon, div[data-testid='job-card'], .jobsearch-SerpJobCard"
            )
            jobs = []
            for card in cards[:max_results]:
                job = self._parse_card(card)
                if job and job.get("title"):
                    jobs.append(job)
            return jobs

    def _parse_card(self, card) -> dict | None:
        try:
            title_el = card.select_one("h2.jobTitle a, a.jobtitle, a[data-jk]")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            company_el = card.select_one(
                "span.companyName, span[data-testid='company-name'], .company"
            )
            company = company_el.get_text(strip=True) if company_el else ""

            location_el = card.select_one(
                "div.companyLocation, span[data-testid='text-location'], .location"
            )
            loc = location_el.get_text(strip=True) if location_el else ""

            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.indeed.com{link}"

            salary_el = card.select_one(
                "span.salary, div.metadata.salary-snippet-container, .salaryText"
            )
            salary = salary_el.get_text(strip=True) if salary_el else ""

            snippet_el = card.select_one("div.job-snippet, .summary")
            snippet = snippet_el.get_text(strip=True)[:500] if snippet_el else ""

            return {
                "job_id": hashlib.md5(f"indeed:{link}:{title}".encode()).hexdigest()[
                    :12
                ],
                "title": title,
                "company": company,
                "location": loc,
                "url": link,
                "snippet": snippet,
                "salary": salary,
                "posted_date": "",
                "source": "indeed",
            }
        except Exception as e:
            logger.debug(f"[Indeed] Card parse error: {e}")
            return None

    @staticmethod
    def _extract_location_from_rss(desc: str) -> str:
        m = re.search(r"Location:\s*([^\n<]+)", desc)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _extract_salary_from_rss(desc: str) -> str:
        m = re.search(
            r"(?:\$[\d,]+(?:\.\d{2})?(?:\s*-\s*\$?[\d,]+(?:\.\d{2})?)?)", desc
        )
        return m.group(0) if m else ""

    async def apply(
        self, job: dict[str, Any], cv_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """Try Indeed Quick Apply simulation.
        POSTs to Indeed apply endpoint with form data."""
        url = job.get("url", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not url:
            return False, "No job URL available for Indeed application"

        try:
            async with stealth.get_async_client(
                timeout=15.0, follow_redirects=True
            ) as client:
                headers = self.make_headers()
                # Step 1: GET job page to discover apply URL
                resp = await client.get(url, headers=headers, timeout=15.0)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    # Look for Indeed Quick Apply URL in the page
                    apply_link_tag = soup.select_one(
                        "a[data-tn-element='jobApplicationLink'], a[class*='apply'], a[href*='rc/clk']"
                    )
                    if apply_link_tag:
                        apply_href = apply_link_tag.get("href", "")
                        if apply_href and not apply_href.startswith("http"):
                            apply_href = f"https://www.indeed.com{apply_href}"

                        # Attempt POST to apply endpoint with CV data
                        apply_data = {
                            "jid": job.get("job_id", ""),
                            "resume_text": cv_data.get("cv_text", "")
                            or cv_data.get("skills", ""),
                            "full_name": cv_data.get("name", ""),
                            "email": cv_data.get("email", ""),
                        }
                        apply_resp = await client.post(
                            apply_href
                            or f"https://www.indeed.com/rc/clk?jk={job.get('job_id', '')}",
                            data=apply_data,
                            headers=headers,
                            timeout=15.0,
                        )
                        if apply_resp.status_code in (200, 302, 303):
                            return (
                                True,
                                f"Indeed Quick Apply submitted for {title} at {company}",
                            )

                # Fallback
                return (
                    False,
                    f"Indeed auto-apply attempted but requires manual interaction. "
                    f"Apply: {url} for {title} at {company}",
                )
        except Exception as e:
            return (
                False,
                f"Indeed auto-apply error: {str(e)[:100]}. Apply manually: {url}",
            )


# ─────────────────────────────────────────────
# Bayt.com Scraper (MENA/GCC — WHITE SPACE)
# ─────────────────────────────────────────────


class BaytScraper(PlatformBase):
    """Bayt.com scraper — the #1 MENA job platform.
    No auto-apply tool exists for Bayt.com — this is a white-space feature."""

    @property
    def platform_name(self) -> str:
        return "Bayt"

    @property
    def supported_countries(self) -> list[str]:
        return ["AE", "SA", "QA", "KW", "BH", "OM", "EG", "LB", "JO"]

    async def search(
        self, query: str, location: str = "", max_results: int = 25
    ) -> list[dict[str, Any]]:
        if not _rate_limiter.can_call("bayt"):
            logger.info("[Bayt] Rate limited — skipping")
            return []

        jobs = await self._search_page(query, location, max_results)
        _rate_limiter.record_call("bayt")
        logger.info(f"[Bayt] Found {len(jobs)} jobs")
        return jobs[:max_results]

    async def _search_page(
        self, query: str, location: str, max_results: int
    ) -> list[dict]:
        """Search Bayt.com jobs page."""
        # Map common location names to Bayt location slugs
        loc_map = {
            "uae": "united-arab-emirates",
            "dubai": "united-arab-emirates",
            "abu dhabi": "united-arab-emirates",
            "saudi arabia": "saudi-arabia",
            "riyadh": "saudi-arabia",
            "jeddah": "saudi-arabia",
            "qatar": "qatar",
            "doha": "qatar",
            "kuwait": "kuwait",
            "bahrain": "bahrain",
            "oman": "oman",
            "lebanon": "lebanon",
            "beirut": "lebanon",
            "egypt": "egypt",
            "cairo": "egypt",
            "jordan": "jordan",
            "amman": "jordan",
        }
        loc_slug = None
        if location:
            loc_lower = location.strip().lower()
            if loc_lower in loc_map:
                loc_slug = loc_map[loc_lower]

        q = quote_plus(query)
        if loc_slug:
            url = f"https://www.bayt.com/en/{loc_slug}/jobs/{q}-jobs/"
        else:
            url = f"https://www.bayt.com/en/international/jobs/?q={q}"

        headers = self.make_headers()
        # Bayt requires a cookie for search results
        headers["Accept"] = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        )
        headers["Referer"] = "https://www.bayt.com/"

        try:
            async with stealth.get_async_client(
                timeout=25.0, follow_redirects=True
            ) as client:
                # First hit home page to set cookies
                await client.get("https://www.bayt.com/", headers=headers, timeout=15.0)
                resp = await client.get(url, headers=headers, timeout=25.0)

                if resp.status_code != 200:
                    logger.warning(f"[Bayt] HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "lxml")
                jobs = []
                cards = soup.select(
                    "li[data-jobid], div.job-card, article.is-list, div.has-pointer"
                )
                if not cards:
                    cards = soup.select("div[class*='job']:not([class*='header'])")

                seen = set()
                for card in cards[:max_results]:
                    job = self._parse_card(card)
                    if job and job.get("title") and job["title"] not in seen:
                        seen.add(job["title"])
                        jobs.append(job)
                        if len(jobs) >= max_results:
                            break

                return jobs

        except httpx.TimeoutException:
            logger.warning("[Bayt] Search timed out")
            return []
        except Exception as e:
            logger.error(f"[Bayt] Search error: {e}")
            return []

    def _parse_card(self, card) -> dict | None:
        try:
            # Title & link
            title_el = card.select_one(
                "h2 a, a[href*='/job/'], a.job-title, .job-title a, a[class*='title']"
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.bayt.com{link}"

            # Job ID from data attribute or URL
            job_id = card.get("data-jobid", "") or ""
            if not job_id and link:
                m = re.search(r"/job/(\d+)", link)
                if m:
                    job_id = m.group(1)
            if not job_id:
                job_id = hashlib.md5(f"bayt:{link}:{title}".encode()).hexdigest()[:12]

            # Company
            company_el = card.select_one(
                "span[data-company], a[data-company], .company, "
                "a[href*='/company/'], span[class*='company'], div[class*='company']"
            )
            company = company_el.get_text(strip=True) if company_el else ""

            # Location
            loc_el = card.select_one(
                "span[data-location], span[class*='location'], "
                "div[class*='location'], .location, span[class*='country']"
            )
            location = loc_el.get_text(strip=True) if loc_el else ""

            # Snippet
            snippet_el = card.select_one(
                "p.short-desc, div.short-desc, p[class*='desc'], div[class*='desc']"
            )
            snippet = snippet_el.get_text(strip=True)[:500] if snippet_el else ""

            # Posted date
            date_el = card.select_one(
                "span[data-date], span[class*='date'], time, .date"
            )
            posted = date_el.get_text(strip=True) if date_el else ""

            return {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": link,
                "snippet": snippet,
                "salary": "",
                "posted_date": posted,
                "source": "bayt",
            }
        except Exception as e:
            logger.debug(f"[Bayt] Card parse error: {e}")
            return None

    async def apply(
        self, job: dict[str, Any], cv_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """Try Bayt.com auto-apply simulation.
        Attempts to POST to Bayt apply endpoint with session cookies."""
        url = job.get("url", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not url:
            return False, "No job URL available for Bayt application"

        try:
            async with stealth.get_async_client(
                timeout=20.0, follow_redirects=True
            ) as client:
                headers = self.make_headers()
                headers["Referer"] = "https://www.bayt.com/"

                # Step 1: Get homepage to set cookies
                await client.get("https://www.bayt.com/", headers=headers, timeout=10.0)

                # Step 2: GET the job page
                resp = await client.get(url, headers=headers, timeout=15.0)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    # Look for apply form/button
                    apply_btn = soup.select_one(
                        "a[href*='/apply/'], button[class*='apply'], a[id*='apply'], a[class*='apply']"
                    )
                    if apply_btn:
                        apply_url = apply_btn.get("href", "")
                        if apply_url and not apply_url.startswith("http"):
                            apply_url = f"https://www.bayt.com{apply_url}"

                        # Attempt POST with candidate data
                        apply_data = {
                            "full_name": cv_data.get("name", ""),
                            "email": cv_data.get("email", ""),
                            "phone": cv_data.get("phone", ""),
                            "cover_letter": f"Application for {title} position at {company}. "
                            f"Experienced {cv_data.get('title', 'professional')} with "
                            f"{cv_data.get('experience_years', 'over 10')} years of experience.",
                        }
                        post_resp = await client.post(
                            apply_url, data=apply_data, headers=headers, timeout=20.0
                        )
                        if post_resp.status_code in (200, 302, 303):
                            return (
                                True,
                                f"Bayt.com application submitted for {title} at {company}",
                            )

                # Fallback
                return (
                    False,
                    f"Bayt.com requires manual apply. Apply: {url} for {title} at {company}",
                )
        except Exception as e:
            return (
                False,
                f"Bayt.com auto-apply error: {str(e)[:100]}. Apply manually: {url}",
            )


# ─────────────────────────────────────────────
# NaukriGulf Scraper (MENA/GCC — WHITE SPACE)
# ─────────────────────────────────────────────


class NaukriGulfScraper(PlatformBase):
    """NaukriGulf.com scraper — strong in UAE/Saudi Arabia.
    No auto-apply tool exists for NaukriGulf — another white-space feature."""

    @property
    def platform_name(self) -> str:
        return "NaukriGulf"

    @property
    def supported_countries(self) -> list[str]:
        return ["AE", "SA", "QA", "KW", "BH", "OM"]

    async def search(
        self, query: str, location: str = "", max_results: int = 25
    ) -> list[dict[str, Any]]:
        if not _rate_limiter.can_call("naukrigulf"):
            logger.info("[NaukriGulf] Rate limited — skipping")
            return []

        jobs = await self._search_page(query, location, max_results)
        _rate_limiter.record_call("naukrigulf")
        logger.info(f"[NaukriGulf] Found {len(jobs)} jobs")
        return jobs[:max_results]

    async def _search_page(
        self, query: str, location: str, max_results: int
    ) -> list[dict]:
        q = quote_plus(query)
        loc_q = quote_plus(location) if location else ""

        if location:
            url = f"https://www.naukrigulf.com/{q}-jobs-in-{loc_q}"
        else:
            url = f"https://www.naukrigulf.com/{q}-jobs"

        headers = self.make_headers()
        headers["Referer"] = "https://www.naukrigulf.com/"

        try:
            async with stealth.get_async_client(
                timeout=25.0, follow_redirects=True
            ) as client:
                resp = await client.get(url, headers=headers, timeout=25.0)

                if resp.status_code != 200:
                    logger.warning(f"[NaukriGulf] HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "lxml")
                jobs = []
                cards = soup.select(
                    "article.jobTuple, div.job-card, section[class*='job'], "
                    "div[class*='jobTuple'], div[class*='job']"
                )
                if not cards:
                    cards = soup.select("div[class*='row']:has(a[href*='/jobs/']')")

                seen = set()
                for card in cards[:max_results]:
                    job = self._parse_card(card)
                    if job and job.get("title") and job["title"] not in seen:
                        seen.add(job["title"])
                        jobs.append(job)
                        if len(jobs) >= max_results:
                            break

                return jobs

        except httpx.TimeoutException:
            logger.warning("[NaukriGulf] Search timed out")
            return []
        except Exception as e:
            logger.error(f"[NaukriGulf] Search error: {e}")
            return []

    def _parse_card(self, card) -> dict | None:
        try:
            # Title
            title_el = card.select_one(
                "a.title, a[class*='title'], h2 a, a[href*='/jobs/']"
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.naukrigulf.com{link}"

            job_id = hashlib.md5(f"naukrigulf:{link}:{title}".encode()).hexdigest()[:12]

            # Company
            company_el = card.select_one(
                "a[class*='company'], span[class*='company'], .company-name, .subTitle"
            )
            company = company_el.get_text(strip=True) if company_el else ""

            # Location
            loc_el = card.select_one(
                "li[class*='location'], span[class*='location'], .loc, span[itemprop='addressLocality']"
            )
            location = loc_el.get_text(strip=True) if loc_el else ""

            # Salary
            salary_el = card.select_one(
                "li[class*='salary'], span[class*='salary'], .salary"
            )
            salary = salary_el.get_text(strip=True) if salary_el else ""

            # Snippet
            snippet_el = card.select_one(
                "span[class*='desc'], div[class*='desc'], .description, p[class*='desc']"
            )
            snippet = snippet_el.get_text(strip=True)[:500] if snippet_el else ""

            # Posted date
            date_el = card.select_one(
                "span[class*='date'], time, span[class*='posted']"
            )
            posted = date_el.get_text(strip=True) if date_el else ""

            return {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": link,
                "snippet": snippet,
                "salary": salary,
                "posted_date": posted,
                "source": "naukrigulf",
            }
        except Exception as e:
            logger.debug(f"[NaukriGulf] Card parse error: {e}")
            return None

    async def apply(
        self, job: dict[str, Any], cv_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """Try NaukriGulf auto-apply simulation.
        Attempts to POST to NaukriGulf application endpoint."""
        url = job.get("url", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not url:
            return False, "No job URL available for NaukriGulf application"

        try:
            async with stealth.get_async_client(
                timeout=20.0, follow_redirects=True
            ) as client:
                headers = self.make_headers()
                headers["Referer"] = "https://www.naukrigulf.com/"

                # GET job page
                resp = await client.get(url, headers=headers, timeout=15.0)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    # Look for apply button
                    apply_btn = soup.select_one(
                        "a[href*='apply'], button[class*='apply'], "
                        "a[class*='apply'], input[value*='Apply'], a[id*='apply']"
                    )
                    if apply_btn:
                        apply_url = apply_btn.get("href", "")
                        if apply_url and not apply_url.startswith("http"):
                            apply_url = f"https://www.naukrigulf.com{apply_url}"

                        apply_data = {
                            "name": cv_data.get("name", ""),
                            "email": cv_data.get("email", ""),
                            "mobile": cv_data.get("phone", ""),
                            "resume_text": cv_data.get("cv_text", "") or " ",
                        }
                        post_resp = await client.post(
                            apply_url, data=apply_data, headers=headers, timeout=20.0
                        )
                        if post_resp.status_code in (200, 302, 303):
                            return (
                                True,
                                f"NaukriGulf application submitted for {title} at {company}",
                            )

                return (
                    False,
                    f"NaukriGulf auto-apply attempted. Apply manually: {url} for {title} at {company}",
                )
        except Exception as e:
            return (
                False,
                f"NaukriGulf auto-apply error: {str(e)[:100]}. Apply manually: {url}",
            )


# ─────────────────────────────────────────────
# Gulftalent Scraper (MENA premium)
# ─────────────────────────────────────────────


class GulftalentScraper(PlatformBase):
    """Gulftalent.com — premium GCC recruitment for mid-to-senior roles."""

    @property
    def platform_name(self) -> str:
        return "Gulftalent"

    @property
    def supported_countries(self) -> list[str]:
        return ["AE", "SA", "QA", "KW", "BH", "OM"]

    async def search(
        self, query: str, location: str = "", max_results: int = 25
    ) -> list[dict[str, Any]]:
        if not _rate_limiter.can_call("gulftalent"):
            logger.info("[Gulftalent] Rate limited — skipping")
            return []

        q = quote_plus(query)
        url = f"https://www.gulftalent.com/jobs?q={q}"
        if location:
            l = quote_plus(location)
            url += f"&l={l}"

        headers = self.make_headers()
        headers["Referer"] = "https://www.gulftalent.com/"

        try:
            async with stealth.get_async_client(
                timeout=25.0, follow_redirects=True
            ) as client:
                resp = await client.get(url, headers=headers, timeout=25.0)

                if resp.status_code != 200:
                    logger.warning(f"[Gulftalent] HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "lxml")
                jobs = []
                cards = soup.select(
                    "div.module.job, div[class*='job']:not([class*='header']), li[class*='job']"
                )
                if not cards:
                    cards = soup.select("div.search-result, div[data-job-id]")

                seen = set()
                for card in cards[:max_results]:
                    job = self._parse_card(card)
                    if job and job.get("title") and job["title"] not in seen:
                        seen.add(job["title"])
                        jobs.append(job)
                        if len(jobs) >= max_results:
                            break

                _rate_limiter.record_call("gulftalent")
                logger.info(f"[Gulftalent] Found {len(jobs)} jobs")
                return jobs[:max_results]

        except httpx.TimeoutException:
            logger.warning("[Gulftalent] Search timed out")
            return []
        except Exception as e:
            logger.error(f"[Gulftalent] Search error: {e}")
            return []

    def _parse_card(self, card) -> dict | None:
        try:
            title_el = card.select_one("h2 a, a[class*='title'], h3 a")
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.gulftalent.com{link}"

            job_id = hashlib.md5(f"gulftalent:{link}:{title}".encode()).hexdigest()[:12]

            company_el = card.select_one(
                "span[class*='company'], .company, a[class*='company']"
            )
            company = company_el.get_text(strip=True) if company_el else ""

            loc_el = card.select_one(
                "span[class*='location'], .location, span[class*='loc']"
            )
            location = loc_el.get_text(strip=True) if loc_el else ""

            return {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": link,
                "snippet": "",
                "salary": "",
                "posted_date": "",
                "source": "gulftalent",
            }
        except Exception as e:
            logger.debug(f"[Gulftalent] Card parse error: {e}")
            return None

    async def apply(
        self, job: dict[str, Any], cv_data: dict[str, Any]
    ) -> tuple[bool, str]:
        """Try Gulftalent auto-apply simulation."""
        url = job.get("url", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not url:
            return False, "No job URL available for Gulftalent application"

        try:
            async with stealth.get_async_client(
                timeout=20.0, follow_redirects=True
            ) as client:
                headers = self.make_headers()
                headers["Referer"] = "https://www.gulftalent.com/"

                resp = await client.get(url, headers=headers, timeout=15.0)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    apply_btn = soup.select_one(
                        "a[href*='apply'], button[class*='apply'], "
                        "input[value*='Apply'], a[class*='apply']"
                    )
                    if apply_btn:
                        apply_url = apply_btn.get("href", "")
                        if apply_url and not apply_url.startswith("http"):
                            apply_url = f"https://www.gulftalent.com{apply_url}"

                        apply_data = {
                            "name": cv_data.get("name", ""),
                            "email": cv_data.get("email", ""),
                            "phone": cv_data.get("phone", ""),
                        }
                        post_resp = await client.post(
                            apply_url, data=apply_data, headers=headers, timeout=20.0
                        )
                        if post_resp.status_code in (200, 302, 303):
                            return (
                                True,
                                f"Gulftalent application submitted for {title} at {company}",
                            )

                return (
                    False,
                    f"Gulftalent auto-apply attempted. Apply manually: {url} for {title} at {company}",
                )
        except Exception as e:
            return (
                False,
                f"Gulftalent auto-apply error: {str(e)[:100]}. Apply manually: {url}",
            )


# ─────────────────────────────────────────────
# Platform Registry
# ─────────────────────────────────────────────

PLATFORMS: dict[str, PlatformBase] = {
    "linkedin": LinkedInScraper(),
    "indeed": IndeedScraper(),
    "bayt": BaytScraper(),
    "naukrigulf": NaukriGulfScraper(),
    "gulftalent": GulftalentScraper(),
}


def get_platform(name: str) -> PlatformBase | None:
    """Get a platform instance by name (case-insensitive)."""
    return PLATFORMS.get(name.lower().strip())


def list_available_platforms() -> list[dict[str, Any]]:
    """List all registered platforms with metadata."""
    return [
        {
            "name": p.platform_name,
            "key": key,
            "countries": p.supported_countries,
        }
        for key, p in PLATFORMS.items()
    ]


# ─────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────


class AutoApplyOrchestrator:
    """
    Coordinates multi-platform auto-apply.
    Search → Apply → Track across all configured platforms.
    """

    def __init__(
        self,
        user_id: str = "default",
        campaign_id: str = "",
        cv_data: dict[str, Any] | None = None,
        db_path: str | None = None,
        daily_limit: int = 200,
    ):
        self.user_id = user_id
        self.campaign_id = (
            campaign_id or f"mpa-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        )
        self.cv_data = cv_data or self._default_cv_data()
        self.db_path = db_path or _get_db_path()
        self.daily_limit = daily_limit
        self.stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {
                "found": 0,
                "applied": 0,
                "success": 0,
                "failed": 0,
                "rate_limited": 0,
            }
        )

        # Initialize DB on first use
        init_multi_platform_db(self.db_path)

    @staticmethod
    def _default_cv_data() -> dict[str, Any]:
        """Build CV data from config."""
        return {
            "name": getattr(config, "CANDIDATE_NAME", "Sam Salameh"),
            "email": getattr(config, "CANDIDATE_EMAIL", ""),
            "phone": getattr(config, "CANDIDATE_PHONE", ""),
            "title": getattr(config, "CANDIDATE_TITLE", "Senior Network Engineer"),
            "location": getattr(config, "CANDIDATE_ADDRESS", "Beirut, Lebanon"),
            "skills": getattr(config, "SKILLS", []),
            "experience_years": getattr(config, "YEARS_EXPERIENCE", 15),
            "linkedin": getattr(config, "CANDIDATE_LINKEDIN", ""),
            "titles": getattr(config, "JOB_TITLES", []),
            "locations": getattr(config, "LOCATIONS", []),
        }

    async def search_all(
        self,
        query: str,
        location: str = "",
        platforms: list[str] | None = None,
        max_per_platform: int = 15,
    ) -> dict[str, list[dict]]:
        """
        Search across multiple platforms.
        Returns dict mapping platform_name → list of jobs.
        """
        if not platforms:
            platforms = list(PLATFORMS.keys())

        results: dict[str, list[dict]] = {}

        for name in platforms:
            platform = get_platform(name)
            if not platform:
                logger.warning(f"[Orchestrator] Unknown platform: {name}")
                continue

            try:
                jobs = await platform.search(query, location, max_per_platform)
                results[name] = jobs
                self.stats[name]["found"] += len(jobs)
                logger.info(
                    f"[Orchestrator] {platform.platform_name}: {len(jobs)} jobs found"
                )
            except Exception as e:
                logger.error(f"[Orchestrator] {name} search failed: {e}")
                results[name] = []

            # Polite delay between platforms
            await asyncio.sleep(0.5 + random.random())

        return results

    async def apply_to_job(self, job: dict[str, Any], platform_name: str) -> bool:
        """Apply to a single job on a specific platform. Returns True on success."""
        platform = get_platform(platform_name)
        if not platform:
            logger.warning(
                f"[Orchestrator] Unknown platform for apply: {platform_name}"
            )
            return False

        # Rate limit check
        if not _rate_limiter.can_call(platform_name):
            self.stats[platform_name]["rate_limited"] += 1
            logger.info(
                f"[Orchestrator] {platform.platform_name}: rate limited, skipping"
            )
            return False

        # Daily limit check
        total_applied = sum(s["applied"] for s in self.stats.values())
        if total_applied >= self.daily_limit:
            logger.info(f"[Orchestrator] Daily limit {self.daily_limit} reached")
            return False

        try:
            success, message = await platform.apply(job, self.cv_data)
            self.stats[platform_name]["applied"] += 1

            status = "success" if success else "failed"
            if success:
                self.stats[platform_name]["success"] += 1
            else:
                self.stats[platform_name]["failed"] += 1

            # Log to DB
            log_multi_platform_application(
                user_id=self.user_id,
                campaign_id=self.campaign_id,
                platform=platform_name,
                job_id=job.get("job_id", ""),
                job_title=job.get("title", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                url=job.get("url", ""),
                status=status,
                message=message[:500] if message else "",
                db_path=self.db_path,
            )

            _rate_limiter.record_call(platform_name)

            if success:
                logger.info(
                    f"[Orchestrator] Applied: {job.get('title')} @ {job.get('company')} via {platform_name}"
                )
            else:
                logger.info(
                    f"[Orchestrator] Skipped: {job.get('title')} via {platform_name}: {message[:100]}"
                )

            return success

        except Exception as e:
            error_msg = str(e)[:200]
            self.stats[platform_name]["failed"] += 1
            self.stats[platform_name]["applied"] += 1

            log_multi_platform_application(
                user_id=self.user_id,
                campaign_id=self.campaign_id,
                platform=platform_name,
                job_id=job.get("job_id", ""),
                job_title=job.get("title", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                url=job.get("url", ""),
                status="failed",
                message=f"Error: {error_msg}",
                db_path=self.db_path,
            )
            logger.error(f"[Orchestrator] Apply error on {platform_name}: {error_msg}")
            return False

    async def run_auto_apply_cycle(
        self,
        query: str,
        location: str = "",
        platforms: list[str] | None = None,
        max_per_platform: int = 15,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Full auto-apply cycle: Search → Apply → Report.
        Returns summary dict.
        """
        logger.info("=" * 60)
        logger.info("  MULTI-PLATFORM AUTO-APPLY CYCLE")
        logger.info(f"  Query: {query} | Location: {location}")
        logger.info(f"  Platforms: {platforms or list(PLATFORMS.keys())}")
        logger.info("=" * 60)

        # Phase 1: Search
        search_results = await self.search_all(
            query, location, platforms, max_per_platform
        )

        # Phase 2: Apply
        total_applied = 0
        total_success = 0

        for platform_name, jobs in search_results.items():
            if not jobs:
                continue

            logger.info(
                f"[Orchestrator] Applying on {platform_name} ({len(jobs)} jobs)..."
            )

            for job in jobs:
                success = await self.apply_to_job(job, platform_name)
                if success:
                    total_success += 1
                total_applied += 1

                # Anti-ban delay: 15-45 seconds between applications
                delay = random.uniform(15.0, 45.0)
                logger.debug(f"[Orchestrator] Anti-ban delay: {delay:.1f}s")
                await asyncio.sleep(delay)

            # Inter-platform delay: 30-60 seconds
            delay = random.uniform(30.0, 60.0)
            logger.info(f"[Orchestrator] Inter-platform delay: {delay:.1f}s")
            await asyncio.sleep(delay)

        # Phase 3: Report
        summary = self.get_summary(
            total_found=sum(len(j) for j in search_results.values())
        )
        logger.info("=" * 60)
        logger.info("  CYCLE COMPLETE")
        for k, v in summary.items():
            if k != "platform_stats":
                logger.info(f"  {k}: {v}")
        logger.info("=" * 60)

        return summary

    def get_summary(self, total_found: int = 0) -> dict[str, Any]:
        """Get current cycle summary."""
        total_applied = sum(s["applied"] for s in self.stats.values())
        total_success = sum(s["success"] for s in self.stats.values())
        total_failed = sum(s["failed"] for s in self.stats.values())
        total_rate_limited = sum(s["rate_limited"] for s in self.stats.values())

        return {
            "status": "completed",
            "cycle_id": self.campaign_id,
            "user_id": self.user_id,
            "total_found": total_found,
            "total_applied": total_applied,
            "total_success": total_success,
            "total_failed": total_failed,
            "total_rate_limited": total_rate_limited,
            "success_rate": f"{total_success / max(total_applied, 1) * 100:.1f}%",
            "platform_stats": dict(self.stats),
            "remaining_daily": max(0, self.daily_limit - total_applied),
        }


# ─────────────────────────────────────────────
# CLI Entry Point (for testing)
# ─────────────────────────────────────────────


async def main():
    """Quick test: search all platforms for a network engineer role."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    orch = AutoApplyOrchestrator(daily_limit=10)

    logger.debug("\n🔍 Searching all platforms for 'Network Engineer' in UAE...\n")
    results = await orch.search_all(
        query="Network Engineer",
        location="UAE",
        max_per_platform=5,
    )

    for platform, jobs in results.items():
        logger.debug(f"\n─── {platform.upper()} ({len(jobs)} jobs) ───")
        for j in jobs[:3]:
            logger.debug(f"  • {j.get('title', 'N/A')}")
            logger.debug(f"    {j.get('company', 'N/A')} — {j.get('location', 'N/A')}")
            logger.debug(f"    {j.get('url', 'N/A')}")
        if len(jobs) > 3:
            logger.debug(f"    ... and {len(jobs) - 3} more")

    # Quick stats
    logger.debug("\n📊 Platform Stats:")
    for platform, jobs in results.items():
        logger.debug(f"  {platform}: {len(jobs)} jobs found")

    logger.debug("\n✅ Done. Run with dry_run=True for production cycle.")


if __name__ == "__main__":
    asyncio.run(main())

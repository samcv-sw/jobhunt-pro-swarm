"""
ANTI-BAN PROTECTION SYSTEM
Ported from demo_user Project - Makes bot look human to avoid detection
"""

import asyncio
import logging
import pathlib
import random
from datetime import UTC, datetime, timedelta

import core.pg_sqlite_shim as sqlite3

logger = logging.getLogger(__name__)


class DailyLimitExceededException(Exception):
    """Raised immediately when the scraper daily cap has been reached.

    This is a hard-stop guard: no scraping attempt should be made once this
    is raised.  The counter resets at the next UTC day boundary.

    Args:
        cap: The configured daily cap that was exceeded.
        count: The current count that triggered the limit.
        resets_at: Human-readable string indicating when the counter resets.
    """

    def __init__(self, cap: int, count: int, resets_at: str = "next day boundary"):
        self.cap = cap
        self.count = count
        self.resets_at = resets_at
        super().__init__(
            f"Daily scraping cap of {cap} reached (current count: {count}). "
            f"Resets at: {resets_at}."
        )

# Dynamic SQLite database path configuration
_base_dir = pathlib.Path(__file__).resolve().parent.parent
try:
    import config

    _db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
    DB_PATH = str(_base_dir / _db_name)
except Exception:
    DB_PATH = str(_base_dir / "jobhunt_saas_v2.db")


class AntiBanProtection:
    """
    Protects email sending from being detected and banned.

    Features:
    - Human-like timing patterns
    - Rate limiting per company
    - Honeypot detection
    - Suspicious company detection
    - Application spacing
    """

    def __init__(self):
        # Track applications per company
        self.company_applications: dict[str, list[datetime]] = {}

        # Blacklist of suspicious/honeypot companies
        self.suspicious_companies: set[str] = set()

        # Track failed applications
        self.failed_applications: dict[str, int] = {}

        # Honeypot indicators
        self.honeypot_keywords = {
            "honeypot",
            "trap",
            "automated",
            "spam",
            "scam",
            "phishing",
            "crawler",
            "scraper",
        }

        # Suspicious patterns
        self.suspicious_patterns = {
            "too_good": [
                "$500k",
                "$1M",
                "million dollar",
                "instant hire",
                "no experience needed",
            ],
            "vague": [
                "various positions",
                "multiple roles",
                "any position",
                "flexible role",
            ],
            "urgent": ["urgent", "immediate", "asap", "right now", "today only"],
            "suspicious_email": [
                "noreply",
                "no-reply",
                "donotreply",
                "test@",
                "admin@",
            ],
        }

        # Rate limits
        self.max_apps_per_company_per_day = 1
        self.max_apps_per_company_per_week = 2
        self.max_apps_per_company_total = 5
        self.min_time_between_apps = 2  # 2 seconds minimum
        self.max_apps_per_hour = 50  # Conservative
        self.max_apps_per_day = 200  # Conservative

        # Timing
        self.last_application_time = None
        self.daily_applications = 0
        self.daily_reset_time = datetime.now()
        self.hourly_applications = 0
        self.hourly_reset_time = datetime.now()

    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for tracking"""
        return company_name.lower().strip().replace(" ", "_")

    def _get_user_key(self, company_key: str, user_id: str | None) -> str:
        """Get unique composite key for tenant + company tracking"""
        uid = user_id or "default"
        return f"{uid}:{company_key}"

    def is_honeypot(self, email: str, company: str, snippet: str = "") -> bool:
        """
        Check if this looks like a honeypot/spam trap.
        Avoids false positives on common hiring terms (urgent, asap) and valid admin emails.
        """
        email_lower = email.lower()
        company_lower = company.lower()
        snippet_lower = snippet.lower()

        # 1. Definitive honeypot indicators (high-confidence blocks)
        definitive_honeypots = {
            "honeypot",
            "spamtrap",
            "crawler-trap",
            "crawler_trap",
            "spam-trap",
        }
        for keyword in definitive_honeypots:
            if (
                keyword in email_lower
                or keyword in company_lower
                or keyword in snippet_lower
            ):
                logger.warning(
                    f"HONEYPOT detected: {company} - '{keyword}' found in target"
                )
                return True

        # 2. Skip obvious test/dev destinations
        test_indicators = {"test@", "example.com", "localhost"}
        for indicator in test_indicators:
            if indicator in email_lower:
                logger.warning(f"Test/Sandbox target skipped: {email}")
                return True

        # 3. Direct noreply addresses should be skipped (useless to send emails to)
        noreply_indicators = {"noreply@", "no-reply@", "donotreply@"}
        for indicator in noreply_indicators:
            if indicator in email_lower:
                logger.info(f"Noreply target skipped: {email}")
                return True

        # Note: We deliberately DO NOT block 'admin@' or common hiring terms like 'urgent',
        # 'immediate', or 'asap' here, as they are standard parts of legitimate recruiting.
        # Specific fraud patterns are handled separately by the ScamDetector.

        return False

    def can_apply_to_company(
        self, company: str, user_id: str | None = None
    ) -> tuple[bool, str]:
        """Check if we can apply to this company (in-memory + database persistence, tenant-isolated)"""
        company_key = self._normalize_company_name(company)
        user_key = self._get_user_key(company_key, user_id)
        now = datetime.now()

        # 1. Check in-memory blacklist first (fastest)
        if user_key in self.suspicious_companies:
            return False, "Company is blacklisted for this tenant (in-memory)"

        # 2. Check in-memory application history (fastest local checks)
        apps = self.company_applications.get(user_key, [])

        # Clean old entries
        apps = [app for app in apps if (now - app).days < 30]
        self.company_applications[user_key] = apps

        # Check in-memory limits
        daily_apps = [app for app in apps if (now - app).days < 1]
        if len(daily_apps) >= self.max_apps_per_company_per_day:
            return (
                False,
                f"Daily limit reached ({self.max_apps_per_company_per_day}/day in-memory)",
            )

        weekly_apps = [app for app in apps if (now - app).days < 7]
        if len(weekly_apps) >= self.max_apps_per_company_per_week:
            return (
                False,
                f"Weekly limit reached ({self.max_apps_per_company_per_week}/week in-memory)",
            )

        if len(apps) >= self.max_apps_per_company_total:
            return (
                False,
                f"Total limit reached ({self.max_apps_per_company_total} total in-memory)",
            )

        # 3. Check historical database counts and blacklist in a single combined query
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                # Detect if user_id column exists in jobs table
                has_user_id = True
                try:
                    conn.execute("SELECT user_id FROM jobs LIMIT 1")
                except Exception:
                    has_user_id = False

                if has_user_id and user_id:
                    cur = conn.execute(
                        """
                        SELECT
                            SUM(CASE WHEN response_type='blacklisted' OR response_type='honeypot' THEN 1 ELSE 0 END),
                            SUM(CASE WHEN status='applied' AND datetime(created_at) >= datetime('now', '-1 day') THEN 1 ELSE 0 END),
                            SUM(CASE WHEN status='applied' AND datetime(created_at) >= datetime('now', '-7 days') THEN 1 ELSE 0 END),
                            SUM(CASE WHEN status='applied' THEN 1 ELSE 0 END)
                        FROM jobs
                        WHERE LOWER(company)=? AND (user_id=? OR user_id IS NULL)
                    """,
                        (company.lower().strip(), user_id),
                    )
                else:
                    cur = conn.execute(
                        """
                        SELECT
                            SUM(CASE WHEN response_type='blacklisted' OR response_type='honeypot' THEN 1 ELSE 0 END),
                            SUM(CASE WHEN status='applied' AND datetime(created_at) >= datetime('now', '-1 day') THEN 1 ELSE 0 END),
                            SUM(CASE WHEN status='applied' AND datetime(created_at) >= datetime('now', '-7 days') THEN 1 ELSE 0 END),
                            SUM(CASE WHEN status='applied' THEN 1 ELSE 0 END)
                        FROM jobs
                        WHERE LOWER(company)=?
                    """,
                        (company.lower().strip(),),
                    )

                row = cur.fetchone()
                if row:
                    is_blacklisted = row[0] or 0
                    db_daily = row[1] or 0
                    db_weekly = row[2] or 0
                    db_total = row[3] or 0

                    if is_blacklisted > 0:
                        self.suspicious_companies.add(user_key)
                        return (
                            False,
                            "Company is blacklisted for this tenant (historical database check)",
                        )
                    if db_daily >= self.max_apps_per_company_per_day:
                        return (
                            False,
                            f"Daily limit reached ({db_daily}/day, database check)",
                        )
                    if db_weekly >= self.max_apps_per_company_per_week:
                        return (
                            False,
                            f"Weekly limit reached ({db_weekly}/week, database check)",
                        )
                    if db_total >= self.max_apps_per_company_total:
                        return (
                            False,
                            f"Total limit reached ({db_total} total, database check)",
                        )
        except Exception as e:
            logger.debug(f"Database query optimization checks failed: {e}")

        return True, "OK"

    def record_application(self, company: str, user_id: str | None = None):
        """Record an application to a company"""
        company_key = self._normalize_company_name(company)
        user_key = self._get_user_key(company_key, user_id)
        now = datetime.now()

        if user_key not in self.company_applications:
            self.company_applications[user_key] = []

        self.company_applications[user_key].append(now)
        self.last_application_time = now
        self.daily_applications += 1
        self.hourly_applications += 1

        logger.debug(
            f"Recorded application to {company} (tenant: {user_id or 'default'})"
        )

    def record_failure(self, company: str, user_id: str | None = None):
        """Record a failed application"""
        company_key = self._normalize_company_name(company)
        user_key = self._get_user_key(company_key, user_id)

        if user_key not in self.failed_applications:
            self.failed_applications[user_key] = 0

        self.failed_applications[user_key] += 1

        # Blacklist after 3 failures
        if self.failed_applications[user_key] >= 3:
            self.suspicious_companies.add(user_key)
            logger.warning(
                f"Blacklisted {company} for tenant {user_id or 'default'} after {self.failed_applications[user_key]} failures"
            )

    def should_blacklist_company(
        self, company: str, user_id: str | None = None
    ) -> bool:
        """Check if company should be blacklisted (in-memory + database check)"""
        company_key = self._normalize_company_name(company)
        user_key = self._get_user_key(company_key, user_id)

        # Check in-memory first
        failures = self.failed_applications.get(user_key, 0)
        if failures >= 3:
            return True
        if user_key in self.suspicious_companies:
            return True

        # Check database
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                # Detect if user_id column exists
                has_user_id = True
                try:
                    conn.execute("SELECT user_id FROM jobs LIMIT 1")
                except Exception:
                    has_user_id = False

                if has_user_id and user_id:
                    cur = conn.execute(
                        """
                        SELECT COUNT(*) FROM jobs
                        WHERE LOWER(company)=? AND (user_id=? OR user_id IS NULL)
                        AND (response_type='blacklisted' OR response_type='honeypot')
                    """,
                        (company.lower().strip(), user_id),
                    )
                else:
                    cur = conn.execute(
                        """
                        SELECT COUNT(*) FROM jobs
                        WHERE LOWER(company)=?
                        AND (response_type='blacklisted' OR response_type='honeypot')
                    """,
                        (company.lower().strip(),),
                    )

                if cur.fetchone()[0] > 0:
                    # Sync to in-memory cache
                    self.suspicious_companies.add(user_key)
                    return True
        except Exception:
            pass

        return False

    def get_delay_before_next(self) -> float:
        """Get delay before next application (human-like)"""
        now = datetime.now()

        # Reset hourly counter
        if (now - self.hourly_reset_time).seconds >= 3600:
            self.hourly_applications = 0
            self.hourly_reset_time = now

        # Reset daily counter
        if (now - self.daily_reset_time).days >= 1:
            self.daily_applications = 0
            self.daily_reset_time = now

        # Check hourly limit
        if self.hourly_applications >= self.max_apps_per_hour:
            # Wait until next hour
            wait_time = 3600 - (now - self.hourly_reset_time).seconds
            logger.warning(f"Hourly limit reached. Waiting {wait_time}s")
            return wait_time

        # Check daily limit
        if self.daily_applications >= self.max_apps_per_day:
            # Wait until tomorrow
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            wait_time = (tomorrow - now).seconds
            logger.warning(f"Daily limit reached. Waiting {wait_time}s")
            return wait_time

        # Base delay with jitter
        base_delay = self.min_time_between_apps
        jitter = random.uniform(0.5, 2.0)  # 0.5-2s jitter
        delay = base_delay + jitter

        # Add extra delay if last application was too recent
        if self.last_application_time:
            time_since_last = (now - self.last_application_time).seconds
            if time_since_last < self.min_time_between_apps:
                extra_delay = self.min_time_between_apps - time_since_last
                delay += extra_delay

        return delay

    async def wait_for_safe_timing(self):
        """Wait for safe timing between applications"""
        delay = self.get_delay_before_next()
        if delay > 0:
            logger.debug(f"Waiting {delay:.1f}s before next application")
            await asyncio.sleep(delay)

    def get_stats(self) -> dict:
        """Get anti-ban statistics"""
        return {
            "daily_applications": self.daily_applications,
            "hourly_applications": self.hourly_applications,
            "blacklisted_companies": len(self.suspicious_companies),
            "tracked_companies": len(self.company_applications),
            "total_failures": sum(self.failed_applications.values()),
        }

    def get_platform_delay(self, url: str) -> float:
        """Get the platform-specific scraper delay (with optional jitter)."""
        return get_platform_delay(url)


# Global instance
anti_ban = AntiBanProtection()


# ---------------------------------------------------------------------------
# Platform-Specific Scraper Delays
# ---------------------------------------------------------------------------

PLATFORM_DELAY_PROFILES = {
    "linkedin.com": {"delay": 3.0, "jitter": True},
    "indeed.com": {"delay": 1.0, "jitter": True},
    "bayt.com": {"delay": 2.0, "jitter": True},
    "default": {"delay": 1.5, "jitter": True}
}

def get_platform_delay(url: str) -> float:
    """Get the platform-specific scraper delay (with optional jitter)."""
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        profile = PLATFORM_DELAY_PROFILES["linkedin.com"]
    elif "indeed.com" in url_lower:
        profile = PLATFORM_DELAY_PROFILES["indeed.com"]
    elif "bayt.com" in url_lower:
        profile = PLATFORM_DELAY_PROFILES["bayt.com"]
    else:
        profile = PLATFORM_DELAY_PROFILES["default"]

    delay = profile["delay"]
    if profile["jitter"]:
        # Add random jitter between 0.5 * delay and 1.5 * delay
        delay = delay * random.uniform(0.5, 1.5)
    return delay



# ---------------------------------------------------------------------------
# R5: Scraper Daily Cap Enforcement
# ---------------------------------------------------------------------------

# Module-level state for the daily scraping cap (shared across all callers in
# the same process, guarded by the AntiBanProtection instance's logic).
_daily_scrape_count: int = 0
_daily_scrape_date: str = ""  # ISO date string, e.g. "2024-01-15"


def _today_str() -> str:
    """Return today's ISO date string (UTC-aware via datetime)."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


def check_daily_scraping_cap(
    cap: int | None = None,
    *,
    increment: bool = True,
) -> int:
    """Check (and optionally increment) the daily scraping counter.

    Must be called **before** initiating a scrape.  Raises
    :class:`DailyLimitExceededException` instantly if the cap has already
    been reached for today.  The counter is reset automatically at the
    UTC day boundary.

    Args:
        cap: Maximum allowed scraping calls per day.  Defaults to
             ``anti_ban.max_apps_per_day``.
        increment: When *True* (default), increment the counter for this
                   call.  Pass *False* to perform a read-only check.

    Returns:
        The updated (or current) daily scraping count.

    Raises:
        DailyLimitExceededException: When the daily cap is already met.
    """
    global _daily_scrape_count, _daily_scrape_date

    if cap is None:
        cap = anti_ban.max_apps_per_day

    today = _today_str()

    # Reset at day boundary
    if _daily_scrape_date != today:
        _daily_scrape_count = 0
        _daily_scrape_date = today

    # Guard: raise *before* incrementing so callers never exceed the cap
    if _daily_scrape_count >= cap:
        tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d 00:00 UTC")
        raise DailyLimitExceededException(
            cap=cap,
            count=_daily_scrape_count,
            resets_at=tomorrow,
        )

    if increment:
        _daily_scrape_count += 1

    return _daily_scrape_count


def reset_daily_scraping_cap() -> None:
    """Manually reset the daily scraping counter (useful for testing)."""
    global _daily_scrape_count, _daily_scrape_date
    _daily_scrape_count = 0
    _daily_scrape_date = _today_str()

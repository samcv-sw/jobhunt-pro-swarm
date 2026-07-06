"""
JobHunt Pro - HYPER MODE Engine
2000+ applications/hour using TEMPLATE mode (zero AI, just fast templates + parallel SMTP)

Port of HYPER_MODE.py from Sam_Job_Automator_Ultimate, adapted for JobHunt Pro.
Integrates with existing config.py, database.py, and orchestrator.py infrastructure.
"""

import logging
import os
import time
import json
import smtplib
import ssl
import threading
import concurrent.futures
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import List, Dict, Optional, Tuple

from dotenv import load_dotenv

import config
from core.turbo_templates import get_letter, detect_template_key

load_dotenv()

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# HYPER MODE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

HYPER_MODE_ENABLED = os.getenv("HYPER_MODE_ENABLED", "true").lower() == "true"
HYPER_TEST_MODE = os.getenv("HYPER_TEST_MODE", "false").lower() == "true"
HYPER_TEST_EMAIL = os.getenv("HYPER_TEST_EMAIL", config.CANDIDATE_EMAIL)
HYPER_PARALLEL_WORKERS = int(os.getenv("HYPER_PARALLEL_WORKERS", "20"))
HYPER_BATCH_SIZE = int(os.getenv("HYPER_BATCH_SIZE", "100"))
HYPER_SMTP_POOL_SIZE = int(os.getenv("HYPER_SMTP_POOL_SIZE", "50"))

# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL PROVIDERS – Loaded from environment (10+ Gmail, 3 Outlook, 3 Zoho)
# ═══════════════════════════════════════════════════════════════════════════════


def load_hyper_providers() -> list:
    """Load all email providers from environment variables.

    Supports:
    - Gmail: GMAIL_SMTP_USER_1..10 + GMAIL_APP_PASSWORD_1..10 (100/day each)
    - Outlook: OUTLOOK_USER_1..3 + OUTLOOK_PASSWORD_1..3 (100/day each)
    - Zoho: ZOHO_USER_1..3 + ZOHO_PASSWORD_1..3 (100/day each)
    """
    providers = []

    # Gmail accounts (up to 10)
    for i in range(1, 11):
        user = os.getenv(f"GMAIL_SMTP_USER_{i}", "").strip()
        pwd = os.getenv(f"GMAIL_APP_PASSWORD_{i}", "").strip()
        if user and pwd:
            providers.append(
                {
                    "name": f"Gmail{i}",
                    "server": "smtp.gmail.com",
                    "port": 587,
                    "email": user,
                    "password": pwd,
                    "daily_limit": 100,
                    "weight": 2,
                }
            )

    # Outlook accounts (up to 3)
    for i in range(1, 4):
        user = os.getenv(f"OUTLOOK_USER_{i}", "").strip()
        pwd = os.getenv(f"OUTLOOK_PASSWORD_{i}", "").strip()
        if user and pwd:
            providers.append(
                {
                    "name": f"Outlook{i}",
                    "server": "smtp-mail.outlook.com",
                    "port": 587,
                    "email": user,
                    "password": pwd,
                    "daily_limit": 100,
                    "weight": 1,
                }
            )

    # Zoho accounts (up to 3)
    for i in range(1, 4):
        user = os.getenv(f"ZOHO_USER_{i}", "").strip()
        pwd = os.getenv(f"ZOHO_PASSWORD_{i}", "").strip()
        if user and pwd:
            providers.append(
                {
                    "name": f"Zoho{i}",
                    "server": "smtp.zoho.com",
                    "port": 587,
                    "email": user,
                    "password": pwd,
                    "daily_limit": 100,
                    "weight": 1,
                }
            )

    # Also load from existing config's EMAIL_PROVIDERS if they have credentials
    for ep in config.EMAIL_PROVIDERS:
        name = ep.get("name", "?")
        # Skip if already loaded via env vars (check by email)
        already = any(p["email"] == ep.get("user", "") for p in providers)
        if not already and ep.get("user") and ep.get("password"):
            providers.append(
                {
                    "name": name,
                    "server": ep.get("server", "smtp.gmail.com"),
                    "port": ep.get("port", 587),
                    "email": ep["user"],
                    "password": ep["password"],
                    "daily_limit": ep.get("daily_limit", 100),
                    "weight": ep.get("weight", 1),
                }
            )

    return providers


# Lazy-loaded providers (deferred from import time to avoid circular import issues)
_providers_cache = None


def get_hyper_providers() -> list:
    global _providers_cache
    if _providers_cache is None:
        _providers_cache = load_hyper_providers()
        logger.info(f"[HYPER] Loaded {len(_providers_cache)} email providers")
        if _providers_cache:
            for p in _providers_cache:
                logger.info(
                    f"[HYPER]   {p['name']}: {p['email']} ({p['daily_limit']}/day via {p['server']})"
                )
    return _providers_cache


# Backward-compat alias
# All code must use get_hyper_providers() for lazy loading; get_hyper_providers() removed


# ═══════════════════════════════════════════════════════════════════════════════
# SMTP CONNECTION POOL – Reuse connections for maximum throughput
# ═══════════════════════════════════════════════════════════════════════════════


class SMTPConnectionPool:
    """Thread-safe SMTP connection pool with keepalive.

    Manages a pool of persistent SMTP connections for each provider.
    Connections are tested with NOOP before reuse and recycled on failure.
    """

    def __init__(self, max_size: int = 50):
        self._pool = {}  # key -> (conn, last_used_timestamp)
        self._lock = threading.Lock()
        self._max_size = max_size
        self._pool_hits = 0
        self._pool_misses = 0

    def _test_connection(self, conn: smtplib.SMTP) -> bool:
        """Test if SMTP connection is alive."""
        try:
            status = conn.noop()
            return status[0] == 250
        except Exception:
            return False

    def get_connection(self, provider: dict) -> Optional[smtplib.SMTP]:
        """Get a cached SMTP connection or create a new one.

        Args:
            provider: Provider dict with server, port, email, password

        Returns:
            Connected SMTP instance, or None on failure
        """
        key = f"{provider['name']}@{provider['server']}"
        now = time.time()

        with self._lock:
            # Check pool
            if key in self._pool:
                conn, last_used = self._pool[key]
                age = now - last_used

                # Recycle if connection is old (>60s idle)
                if age > 60 or not self._test_connection(conn):
                    try:
                        conn.quit()
                    except Exception:
                        pass
                    del self._pool[key]
                else:
                    self._pool[key] = (conn, now)
                    self._pool_hits += 1
                    logger.debug(f"[SMTP-POOL] HIT {key} (age={age:.0f}s)")
                    return conn

        # Create new connection
        try:
            conn = smtplib.SMTP(provider["server"], provider["port"], timeout=10)
            conn.ehlo()
            conn.starttls(context=ssl.create_default_context())
            conn.ehlo()
            conn.login(provider["email"], provider["password"])

            with self._lock:
                # Evict oldest if pool is full
                if len(self._pool) >= self._max_size:
                    oldest_key = min(self._pool.keys(), key=lambda k: self._pool[k][1])
                    try:
                        self._pool[oldest_key][0].quit()
                    except Exception:
                        pass
                    del self._pool[oldest_key]

                self._pool[key] = (conn, now)
                self._pool_misses += 1
                logger.debug(f"[SMTP-POOL] MISS {key} (pool={len(self._pool)})")

            return conn
        except Exception as e:
            logger.warning(f"[SMTP-POOL] Failed to connect {key}: {e}")
            return None

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for key, (conn, _) in self._pool.items():
                try:
                    conn.quit()
                except Exception:
                    pass
            self._pool.clear()
            logger.info(
                f"[SMTP-POOL] Closed all connections (hits={self._pool_hits}, misses={self._pool_misses})"
            )

    def get_stats(self) -> dict:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "pool_hits": self._pool_hits,
                "pool_misses": self._pool_misses,
                "max_size": self._max_size,
            }


# Global SMTP connection pool
smtp_pool = SMTPConnectionPool(max_size=HYPER_SMTP_POOL_SIZE)


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL PROVIDER ROTATOR – Distributes load across providers
# ═══════════════════════════════════════════════════════════════════════════════


class ProviderRotator:
    """Round-robin provider rotator with daily rate-limit tracking.

    Ensures no provider exceeds its daily limit. Resets counts every 24 hours.
    """

    def __init__(self, providers: list):
        self.providers = [p for p in providers if p.get("email") and p.get("password")]
        self.index = 0
        self.daily_counts = defaultdict(int)
        self.last_reset = time.time()

    def get_next(self) -> Optional[dict]:
        """Get next available provider (round-robin, respecting daily limits)."""
        # Reset daily counts every 24 hours
        if time.time() - self.last_reset > 86400:
            self.daily_counts = defaultdict(int)
            self.last_reset = time.time()

        if not self.providers:
            return None

        # Try each provider
        for _ in range(len(self.providers)):
            provider = self.providers[self.index % len(self.providers)]
            self.index += 1

            if self.daily_counts[provider["name"]] < provider["daily_limit"]:
                return provider

        return None  # All providers rate-limited

    def record_send(self, provider_name: str):
        """Record a successful send for a provider."""
        self.daily_counts[provider_name] += 1

    def get_stats(self) -> dict:
        """Get provider usage statistics."""
        return {
            "total_providers": len(self.providers),
            "daily_sends": dict(self.daily_counts),
            "daily_limits": {p["name"]: p["daily_limit"] for p in self.providers},
            "total_sent_today": sum(self.daily_counts.values()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HYPER EMAIL ENGINE – Parallel SMTP email sender
# ═══════════════════════════════════════════════════════════════════════════════


class HyperEmailEngine:
    """High-performance parallel email engine.

    Sends multiple emails concurrently using ThreadPoolExecutor + SMTP connection pool.
    No AI calls, no delays. Pure template + raw SMTP speed.
    """

    def __init__(self, max_workers: int = 20):
        self.rotator = ProviderRotator(get_hyper_providers())
        self.max_workers = max_workers
        self.sent_count = 0
        self.fail_count = 0
        self._start_time = None

    def send_parallel(self, applications: List[Dict]) -> Tuple[List[str], int, int]:
        """Send multiple applications in parallel using ThreadPoolExecutor.

        Args:
            applications: List of dicts with 'email', 'title', 'company', 'letter' keys.
                          Also accepts 'job_id' and 'hr_email' as email field aliases.

        Returns:
            Tuple of (successful_email_addresses, sent_count, fail_count)
        """
        self._start_time = time.time()
        self.sent_count = 0
        self.fail_count = 0

        if not self.rotator.providers:
            logger.error(
                "[HYPER] No email providers configured! Add GMAIL/OUTLOOK/ZOHO credentials to .env"
            )
            return [], 0, len(applications)

        successful = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all tasks
            future_to_app = {
                executor.submit(self._send_one, app): app for app in applications
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_app):
                app = future_to_app[future]
                try:
                    result = future.result()
                    if result:
                        successful.append(app.get("email") or app.get("hr_email"))
                        self.sent_count += 1
                    else:
                        self.fail_count += 1
                except Exception as e:
                    logger.error(
                        f"[HYPER] Send failed for {app.get('company', '?')}: {e}"
                    )
                    self.fail_count += 1

        return successful, self.sent_count, self.fail_count

    def _send_one(self, app: Dict) -> bool:
        """Send a single application email.

        Args:
            app: Dict with 'title', 'company', 'letter' and either 'email' or 'hr_email'

        Returns:
            True if sent successfully, False otherwise
        """
        recipient = app.get("email") or app.get("hr_email", "")
        if not recipient:
            logger.warning(f"[HYPER] No email for {app.get('company', '?')}")
            return False

        # Test mode: redirect to test email
        if HYPER_TEST_MODE:
            recipient = HYPER_TEST_EMAIL

        # Get next available provider
        provider = self.rotator.get_next()
        if not provider:
            logger.warning("[HYPER] All providers rate-limited for today")
            return False

        try:
            # Build email
            msg = MIMEMultipart("mixed")
            msg["Subject"] = f"Application: {app['title']} - {config.CANDIDATE_NAME}"
            msg["From"] = f"{config.CANDIDATE_NAME} <{provider['email']}>"
            msg["To"] = recipient
            msg["Reply-To"] = config.CANDIDATE_EMAIL
            msg["Date"] = formatdate(localtime=True)

            # HTML body with professional formatting
            html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:15px;font-family:Arial,sans-serif;background:#f5f5f5;">
<table style="max-width:600px;margin:0 auto;background:#fff;padding:25px;border-radius:8px;">
<tr><td>
<pre style="white-space:pre-wrap;font-family:Arial,sans-serif;line-height:1.6;font-size:13px;">{app["letter"]}</pre>
<hr style="border:none;border-top:1px solid #eee;margin:15px 0;">
<p style="font-size:11px;color:#666;">
<strong>{config.CANDIDATE_NAME}</strong><br>
{config.CANDIDATE_TITLE}<br>
📧 {config.CANDIDATE_EMAIL}<br>
📱 {config.CANDIDATE_PHONE}<br>
🔗 <a href="{config.CANDIDATE_LINKEDIN}" style="color:#0a66c2;">LinkedIn</a>
</p>
</td></tr></table></body></html>"""

            msg.attach(MIMEText(html, "html"))

            # Try pool first, direct connection fallback
            conn = smtp_pool.get_connection(provider)
            if conn:
                refused_pool = conn.send_message(msg)
                if refused_pool:
                    logger.warning(
                        f"[HYPER] Refused via pool {provider['name']}: {refused_pool}"
                    )
                    return False
                self.rotator.record_send(provider["name"])
                return True

            # Fallback: direct connection
            conn = smtplib.SMTP(provider["server"], provider["port"], timeout=10)
            conn.ehlo()
            conn.starttls(context=ssl.create_default_context())
            conn.ehlo()
            conn.login(provider["email"], provider["password"])
            refused_direct = conn.send_message(msg)
            conn.quit()
            if refused_direct:
                logger.warning(
                    f"[HYPER] Refused via direct {provider['name']}: {refused_direct}"
                )
                return False
            self.rotator.record_send(provider["name"])
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"[HYPER] Auth failed for {provider['name']} ({provider['email']}): {e}"
            )
            return False
        except smtplib.SMTPRecipientsRefused:
            logger.warning(f"[HYPER] Recipient refused: {recipient}")
            return False
        except smtplib.SMTPSenderRefused:
            logger.warning(f"[HYPER] Sender refused: {provider['email']}")
            return False
        except smtplib.SMTPDataError as e:
            logger.warning(f"[HYPER] SMTP data error: {e}")
            return False
        except Exception as e:
            logger.debug(
                f"[HYPER] Send error for {app.get('company', '?')} via {provider['name']}: {e}"
            )
            return False

    def get_stats(self) -> dict:
        """Get send statistics."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        return {
            "sent": self.sent_count,
            "failed": self.fail_count,
            "total": self.sent_count + self.fail_count,
            "elapsed_seconds": round(elapsed, 1),
            "emails_per_hour": round(self.sent_count / elapsed * 3600, 0)
            if elapsed > 0
            else 0,
            "provider_stats": self.rotator.get_stats(),
            "pool_stats": smtp_pool.get_stats(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HYPER SCRAPER – Fast job scraping (no AI, no heavy parsing)
# ═══════════════════════════════════════════════════════════════════════════════


class HyperScraper:
    """Lightweight multi-source job scraper for hyper mode.

    Uses requests + basic HTML parsing. No Selenium, no heavy dependencies.
    Designed for speed, not comprehensive coverage.
    """

    def __init__(self):
        self.session = self._create_session()

    def _create_session(self):
        import requests

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        session.timeout = 10
        return session

    def scrape(self, config_locations: list = None) -> List[Dict]:
        """Scrape jobs from multiple sources in parallel.

        Args:
            config_locations: List of location strings to search. Defaults to config.LOCATIONS[:3]

        Returns:
            List of job dicts with 'title', 'company', 'url', 'source', 'location'
        """
        locations = (config_locations or config.LOCATIONS[:3])[:5]

        jobs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for loc in locations:
                futures.append(executor.submit(self._scrape_source, "bayt", loc))
                futures.append(executor.submit(self._scrape_source, "indeed", loc))

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=15)
                    jobs.extend(result)
                except concurrent.futures.TimeoutError:
                    logger.warning("[HYPER] Scrape timeout for source")
                except Exception as e:
                    logger.error(f"[HYPER] Scrape error: {type(e).__name__}: {e}")

        # Filter for relevant titles
        relevant = [j for j in jobs if self._is_relevant(j.get("title", ""))]

        # Deduplicate by URL
        seen = set()
        unique = []
        for j in relevant:
            url = j.get("url", j.get("title", ""))
            if url not in seen:
                seen.add(url)
                unique.append(j)

        logger.info(
            f"[HYPER] Scraped {len(jobs)} jobs, {len(relevant)} relevant, {len(unique)} unique"
        )
        return unique

    def _scrape_source(self, source: str, location: str) -> List[Dict]:
        """Scrape a single source for a single location."""
        import re

        try:
            if source == "bayt":
                loc_slug = location.lower().replace(" ", "-")
                url = f"https://www.bayt.com/en/{loc_slug}/jobs/network-engineer-jobs/"
            elif source == "indeed":
                # Map locations to Indeed domains
                domain_map = {
                    "lebanon": "lb",
                    "beirut": "lb",
                    "uae": "ae",
                    "dubai": "ae",
                    "abu dhabi": "ae",
                    "saudi arabia": "sa",
                    "riyadh": "sa",
                    "jeddah": "sa",
                    "qatar": "qa",
                    "doha": "qa",
                    "kuwait": "kw",
                }
                domain = domain_map.get(location.lower(), "com")
                url = f"https://{domain}.indeed.com/jobs?q=network+engineer&l={location.replace(' ', '+')}"
            else:
                return []

            r = self.session.get(url, timeout=10)
            if r.status_code != 200:
                return []

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.content, "html.parser")
            jobs = []

            if source == "bayt":
                for card in soup.find_all(
                    "div", class_=re.compile("job-listing|result|card", re.I)
                )[:20]:
                    try:
                        t_el = card.find("h2") or card.find(
                            "a", class_=re.compile("title", re.I)
                        )
                        c_el = card.find(
                            "span", class_=re.compile("company", re.I)
                        ) or card.find("div", class_=re.compile("company", re.I))
                        a_el = card.find("a", href=True)
                        href = ""
                        if a_el:
                            href = a_el["href"]
                            if href.startswith("/"):
                                href = "https://www.bayt.com" + href
                        title = (
                            t_el.get_text(strip=True) if t_el else "Network Engineer"
                        )
                        company = c_el.get_text(strip=True) if c_el else "Company"
                        jobs.append(
                            {
                                "title": title,
                                "company": company,
                                "url": href,
                                "source": f"Bayt {location}",
                                "location": location,
                            }
                        )
                    except Exception:
                        pass

            elif source == "indeed":
                for card in soup.find_all(
                    "div", class_=re.compile("job_seen_beacon|card", re.I)
                )[:20]:
                    try:
                        t_el = card.find(
                            "h2", class_=re.compile("jobTitle", re.I)
                        ) or card.find("a", class_=re.compile("title", re.I))
                        c_el = card.find(
                            "span", class_=re.compile("companyName", re.I)
                        ) or card.find("div", class_=re.compile("company", re.I))
                        a_el = card.find("a", href=True)
                        href = (
                            "https://" + domain + ".indeed.com" + a_el["href"]
                            if a_el and a_el.get("href", "").startswith("/")
                            else (a_el["href"] if a_el else "")
                        )
                        title = (
                            t_el.get_text(strip=True) if t_el else "Network Engineer"
                        )
                        company = c_el.get_text(strip=True) if c_el else "Company"
                        jobs.append(
                            {
                                "title": title,
                                "company": company,
                                "url": href,
                                "source": f"Indeed {location}",
                                "location": location,
                            }
                        )
                    except Exception:
                        pass

            return jobs

        except Exception:
            return []

    def _is_relevant(self, title: str) -> bool:
        """Check if a job title is relevant for a Network Engineer."""
        t = title.lower()
        include = [
            "network",
            "cisco",
            "mikrotik",
            "fortinet",
            "firewall",
            "vpn",
            "routing",
            "infrastructure",
            "security",
            "system admin",
            "noc",
            "telecom",
            "wan",
            "lan",
            "switch",
            "router",
            "engineer",
            "administrator",
            "specialist",
            "technician",
            "architect",
            "manager",
            "operations",
            "support",
        ]
        exclude = [
            "software",
            "web developer",
            "frontend",
            "backend",
            "full stack",
            "mobile",
            "data scientist",
            "marketing",
            "sales",
            "graphic",
            "content",
            "accountant",
            "hr ",
            "human resources",
            "driver",
            "cleaner",
            "waiter",
            "junior",
            "trainee",
            "intern",
        ]
        return any(word in t for word in include) and not any(
            word in t for word in exclude
        )


# ═══════════════════════════════════════════════════════════════════════════════
# HYPER DB WRAPPER – Fast synchronous SQLite tracking for hyper mode
# ═══════════════════════════════════════════════════════════════════════════════


class HyperDB:
    """High-performance local SQLite tracking for hyper mode.

    Separate from the async SQLAlchemy database.py to avoid lock contention.
    Uses WAL mode + immediate transactions for maximum parallel throughput.
    All operations are synchronous for simplicity and speed.
    """

    def __init__(self, path: str = None):
        """Initialize HyperDB with a SQLite database file.

        Args:
            path: Path to SQLite file. Defaults to hyper_jobs.db in project root.
        """
        if path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(project_root, "hyper_jobs.db")
        self.path = path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=30) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS hyper_jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        company TEXT,
                        url TEXT UNIQUE,
                        source TEXT,
                        location TEXT,
                        email TEXT,
                        status TEXT DEFAULT 'pending',
                        template_key TEXT,
                        hr_email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent_at TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS hyper_sends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INTEGER,
                        company TEXT,
                        title TEXT,
                        recipient TEXT,
                        provider TEXT,
                        status TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_hyper_jobs_status ON hyper_jobs(status);
                    CREATE INDEX IF NOT EXISTS idx_hyper_jobs_url ON hyper_jobs(url);
                """)
            logger.info(f"[HYPER-DB] Initialized at {self.path}")
        except Exception as e:
            logger.error(f"[HYPER-DB] Init failed: {e}")

    def add_batch(self, jobs: List[Dict]) -> int:
        """Insert a batch of jobs, skipping duplicates.

        Args:
            jobs: List of job dicts with title, company, url, source, location

        Returns:
            Number of new jobs inserted
        """
import core.pg_sqlite_shim as sqlite3

        count = 0
        try:
            with sqlite3.connect(self.path, timeout=30) as conn:
                for job in jobs:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO hyper_jobs (title, company, url, source, location, email, template_key) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                job.get("title", ""),
                                job.get("company", ""),
                                job.get("url", ""),
                                job.get("source", ""),
                                job.get("location", ""),
                                job.get("email", ""),
                                detect_template_key(job.get("title", "")),
                            ),
                        )
                        if conn.total_changes > count:
                            count += 1
                    except Exception:
                        pass
                conn.commit()
            logger.info(f"[HYPER-DB] Added {count} new jobs")
        except Exception as e:
            logger.error(f"[HYPER-DB] Batch insert failed: {e}")
        return count

    def get_pending(self, limit: int = 1000) -> List[Dict]:
        """Get pending jobs that haven't been applied to.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of job dicts with all fields
        """
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=10) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM hyper_jobs WHERE status='pending' ORDER BY created_at ASC LIMIT ?",
                    (limit,),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"[HYPER-DB] Get pending failed: {e}")
            return []

    def mark_sent(self, job_ids: List[int]):
        """Mark jobs as sent.

        Args:
            job_ids: List of job database IDs to mark as sent
        """
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=10) as conn:
                for jid in job_ids:
                    conn.execute(
                        "UPDATE hyper_jobs SET status='sent', sent_at=CURRENT_TIMESTAMP WHERE id=?",
                        (jid,),
                    )
                conn.commit()
        except Exception as e:
            logger.error(f"[HYPER-DB] Mark sent failed: {e}")

    def log_sends(self, sends: List[Tuple]):
        """Log individual send records.

        Args:
            sends: List of tuples (job_id, company, title, recipient, provider, status)
        """
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=10) as conn:
                for job_id, company, title, recipient, provider, status in sends:
                    try:
                        conn.execute(
                            "INSERT INTO hyper_sends (job_id, company, title, recipient, provider, status) VALUES (?, ?, ?, ?, ?, ?)",
                            (job_id, company, title, recipient, provider, status),
                        )
                    except Exception:
                        pass
                conn.commit()
        except Exception as e:
            logger.error(f"[HYPER-DB] Log sends failed: {e}")

    def is_duplicate(self, url: str) -> bool:
        """Check if a URL has already been processed.

        Args:
            url: Job URL to check

        Returns:
            True if URL already exists in database
        """
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=5) as conn:
                result = conn.execute(
                    "SELECT 1 FROM hyper_jobs WHERE url=? LIMIT 1", (url,)
                ).fetchone()
                return result is not None
        except Exception:
            return False

    def get_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dict with total, sent, pending, fail counts
        """
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=5) as conn:
                total = conn.execute("SELECT COUNT(*) FROM hyper_jobs").fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM hyper_jobs WHERE status='pending'"
                ).fetchone()[0]
                sent = conn.execute(
                    "SELECT COUNT(*) FROM hyper_jobs WHERE status='sent'"
                ).fetchone()[0]
                sends = conn.execute("SELECT COUNT(*) FROM hyper_sends").fetchone()[0]
                return {
                    "total": total,
                    "pending": pending,
                    "sent": sent,
                    "fail": total - pending - sent,
                    "sends": sends,
                }
        except Exception:
            return {"total": 0, "pending": 0, "sent": 0, "fail": 0, "sends": 0}

    def to_json(self, path: str = None) -> str:
        """Export all data to JSON.

        Args:
            path: Output file path. If None, returns JSON string.

        Returns:
            JSON string if path is None
        """
import core.pg_sqlite_shim as sqlite3

        try:
            with sqlite3.connect(self.path, timeout=5) as conn:
                conn.row_factory = sqlite3.Row
                jobs = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT * FROM hyper_jobs ORDER BY created_at DESC"
                    ).fetchall()
                ]
                sends = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT * FROM hyper_sends ORDER BY sent_at DESC LIMIT 1000"
                    ).fetchall()
                ]
                data = {"stats": self.get_stats(), "jobs": jobs, "sends": sends}
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, default=str)
                    logger.info(f"[HYPER-DB] Exported to {path}")
                    return ""
                return json.dumps(data, indent=2, default=str)
        except Exception as e:
            logger.error(f"[HYPER-DB] Export failed: {e}")
            return "{}"


# ═══════════════════════════════════════════════════════════════════════════════
# HYPER MODE ORCHESTRATOR – Main entry point
# ═══════════════════════════════════════════════════════════════════════════════


class HyperMode:
    """Hyper Mode main orchestrator.

    Phases:
    1. Fast parallel scrape from 10+ sources
    2. Template-based cover letter generation (zero AI)
    3. Parallel SMTP blast via connection pool + provider rotator
    4. Database tracking and status reporting

    Estimated throughput: 2000+ applications/hour with 10+ providers.
    """

    def __init__(self):
        self.db = HyperDB()
        self.scraper = HyperScraper()
        self.email = HyperEmailEngine(max_workers=HYPER_PARALLEL_WORKERS)
        self.start_time = None

    def run(self, scrape: bool = True, max_jobs: int = None) -> dict:
        """Execute a full Hyper Mode cycle.

        Args:
            scrape: Whether to scrape for new jobs. If False, uses pending jobs only.
            max_jobs: Maximum number of jobs to process. Defaults to HYPER_BATCH_SIZE.

        Returns:
            Dict with cycle results (scraped, generated, sent, failed, stats)
        """
        self.start_time = time.time()
        batch_size = max_jobs or HYPER_BATCH_SIZE

        logger.info("=" * 70)
        logger.info("[HYPER] HYPER MODE - EXTREME PERFORMANCE")
        logger.info(
            f"   Providers: {len(get_hyper_providers())} | Workers: {HYPER_PARALLEL_WORKERS} | Batch: {batch_size}"
        )
        logger.info("=" * 70)

        results = {
            "new_jobs": 0,
            "generated": 0,
            "sent": 0,
            "failed": 0,
            "elapsed_seconds": 0,
            "emails_per_hour": 0,
        }

        # Phase 1: Scrape (optional)
        if scrape:
            logger.info("\n[PHASE1] PHASE 1: Parallel scraping...")
            jobs = self.scraper.scrape()
            new_jobs = self.db.add_batch(jobs)
            results["new_jobs"] = new_jobs
            logger.info(f"[OK] Scraped {len(jobs)} jobs, {new_jobs} new")

        # Phase 2: Get pending jobs
        pending = self.db.get_pending(batch_size)
        if not pending:
            logger.info("\n[EMPTY] No pending jobs - nothing to send")
            results["elapsed_seconds"] = round(time.time() - self.start_time, 1)
            return results

        logger.info(f"\n[PHASE2] PHASE 2: Processing {len(pending)} pending jobs...")

        # Phase 3: Generate cover letters (zero AI, pure templates)
        logger.info("\n[PHASE3] PHASE 3: Generating cover letters (template mode)...")

        hr_emails = self._guess_hr_emails(pending)
        applications = []
        job_ids = []

        for job, hr_email in zip(pending, hr_emails):
            letter = get_letter(job["title"], job["company"])
            applications.append(
                {
                    "job_id": job["id"],
                    "company": job["company"],
                    "title": job["title"],
                    "email": hr_email,
                    "letter": letter,
                    "template_key": job.get("template_key", "default"),
                }
            )
            job_ids.append(job["id"])

        results["generated"] = len(applications)
        logger.info(f"[OK] Generated {len(applications)} cover letters (template mode)")

        # Phase 4: Parallel email blast
        logger.info(f"\n[PHASE4] PHASE 4: Sending {len(applications)} emails...")

        successful_emails, sent_count, fail_count = self.email.send_parallel(
            applications
        )

        # Log sends to DB
        sends_to_log = []
        for app, success in zip(
            applications, [True] * sent_count + [False] * fail_count
        ):
            sends_to_log.append(
                (
                    app["job_id"],
                    app["company"],
                    app["title"],
                    app["email"],
                    "",
                    "sent" if success else "failed",
                )
            )
        self.db.log_sends(sends_to_log)

        # Mark successfully sent jobs
        if sent_count > 0:
            self.db.mark_sent(job_ids[:sent_count])

        results["sent"] = sent_count
        results["failed"] = fail_count

        # Final stats
        elapsed = time.time() - self.start_time
        results["elapsed_seconds"] = round(elapsed, 1)
        results["emails_per_hour"] = (
            round(sent_count / elapsed * 3600, 0) if elapsed > 0 else 0
        )

        # Add engine stats
        engine_stats = self.email.get_stats()
        results["engine_stats"] = engine_stats
        db_stats = self.db.get_stats()
        results["db_stats"] = db_stats

        logger.info("\n" + "=" * 70)
        logger.info("[DONE] HYPER MODE COMPLETE")
        logger.info(f"   Time:       {results['elapsed_seconds']:.1f}s")
        logger.info(f"   New jobs:   {results['new_jobs']}")
        logger.info(f"   Generated:  {results['generated']}")
        logger.info(f"   Sent:       {results['sent']}")
        logger.info(f"   Failed:     {results['failed']}")
        logger.info(f"   Speed:      {results['emails_per_hour']:.0f} emails/hour")
        logger.info(f"   DB total:   {db_stats.get('total', 0)} jobs")
        logger.info(f"   Providers:  {len(get_hyper_providers())}")
        logger.info("=" * 70)

        return results

    def run_async(self, scrape: bool = True, max_jobs: int = None) -> dict:
        """Run Hyper Mode synchronously (wraps run() in event loop compat).

        Args:
            scrape: Whether to scrape for new jobs
            max_jobs: Maximum jobs to process

        Returns:
            Dict with cycle results
        """
        return self.run(scrape=scrape, max_jobs=max_jobs)

    def _guess_hr_emails(self, jobs: List[Dict]) -> List[str]:
        """Guess HR email addresses from company names.

        Simple heuristic: hr@company.com
        For a production system, integrate with curated_contacts or a CRM.
        """
        emails = []
        for job in jobs:
            # Try to use existing email from job
            if job.get("email"):
                emails.append(job["email"])
                continue

            # Generate from company name
            domain = job.get("company", "company").lower().strip()
            domain = (
                domain.replace(" ", "")
                .replace("'", "")
                .replace(".", "")
                .replace("&", "and")
            )
            domain = domain.replace(",", "").replace("-", "").replace("_", "")

            # Keep domain short but recognizable
            if len(domain) > 30:
                domain = domain[:30]

            emails.append(f"hr@{domain}.com")

        return emails

    def close(self):
        """Clean up resources."""
        smtp_pool.close_all()
        logger.info("[HYPER] Resources cleaned up")

    def get_report(self) -> dict:
        """Get a comprehensive status report."""
        return {
            "status": "ready" if get_hyper_providers() else "no_providers",
            "providers": len(get_hyper_providers()),
            "provider_list": [p["name"] for p in get_hyper_providers()],
            "db": self.db.get_stats(),
            "email": self.email.get_stats(),
            "pool": smtp_pool.get_stats(),
            "config": {
                "enabled": HYPER_MODE_ENABLED,
                "test_mode": HYPER_TEST_MODE,
                "parallel_workers": HYPER_PARALLEL_WORKERS,
                "batch_size": HYPER_BATCH_SIZE,
                "pool_size": HYPER_SMTP_POOL_SIZE,
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    """Run Hyper Mode from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="JobHunt Pro - Hyper Mode")
    parser.add_argument(
        "--no-scrape", action="store_true", help="Skip scraping, use pending jobs only"
    )
    parser.add_argument(
        "--max-jobs", type=int, default=None, help="Max jobs to process"
    )
    parser.add_argument("--report", action="store_true", help="Show status report only")
    parser.add_argument(
        "--export", type=str, default=None, help="Export DB to JSON file"
    )
    parser.add_argument(
        "--providers", action="store_true", help="List loaded providers"
    )

    args = parser.parse_args()

    import os as _os

    _os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/hyper_mode.log", encoding="utf-8"),
        ],
    )

    hyper = HyperMode()
    try:
        if args.report:
            report = hyper.get_report()
            print(json.dumps(report, indent=2, default=str))
            return

        if args.export:
            hyper.db.to_json(args.export)
            return

        if args.providers:
            print(f"\n📧 Loaded {len(get_hyper_providers())} email providers:")
            for p in get_hyper_providers():
                print(f"   {p['name']}: {p['email']} ({p['daily_limit']}/day)")
            return

        result = hyper.run(scrape=not args.no_scrape, max_jobs=args.max_jobs)

        # Print summary
        print(f"\n{'=' * 50}")
        print("📊 HYPER MODE SUMMARY")
        print(f"{'=' * 50}")
        print(f"  New jobs scraped:  {result.get('new_jobs', 0)}")
        print(f"  Letters generated: {result.get('generated', 0)}")
        print(f"  Emails sent:       {result.get('sent', 0)}")
        print(f"  Failed:            {result.get('failed', 0)}")
        print(f"  Time:              {result.get('elapsed_seconds', 0)}s")
        print(f"  Speed:             {result.get('emails_per_hour', 0):.0f}/hour")
        print(f"{'=' * 50}")

    finally:
        hyper.close()


if __name__ == "__main__":
    main()

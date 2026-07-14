import json
import logging
import os
import random
import re
import time
import tracemalloc
import urllib.request
from functools import wraps
from typing import Callable

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# IMP-040: Memory profiling decorator using tracemalloc ────────────────────
MEMORY_WARN_THRESHOLD_MB = float(os.getenv("MEMORY_WARN_MB", "50"))


def profile_memory(fn: Callable) -> Callable:
    """Decorator that profiles peak memory usage of a function using tracemalloc.

    Logs peak allocation in MB after each call. Emits WARNING if peak exceeds
    MEMORY_WARN_THRESHOLD_MB (default 50MB) to catch memory leaks early.
    Works for both sync and async functions.
    """
    import asyncio

    @wraps(fn)
    def sync_wrapper(*args, **kwargs):
        tracemalloc.start()
        try:
            result = fn(*args, **kwargs)
        finally:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak_mb = peak / 1_048_576
            log = logger.warning if peak_mb > MEMORY_WARN_THRESHOLD_MB else logger.debug
            log("[MemProfile] %s peak=%.2f MB", fn.__qualname__, peak_mb)
        return result

    @wraps(fn)
    async def async_wrapper(*args, **kwargs):
        tracemalloc.start()
        try:
            result = await fn(*args, **kwargs)
        finally:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak_mb = peak / 1_048_576
            log = logger.warning if peak_mb > MEMORY_WARN_THRESHOLD_MB else logger.debug
            log("[MemProfile] %s peak=%.2f MB", fn.__qualname__, peak_mb)
        return result

    return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper


class ProxyManager:
    """
    Manages free proxies scraped from free-proxy-list.net and sslproxies.org.
    Caches them to cache/proxy_pool.json, validates, and rotates them.
    """
    def __init__(self, cache_path="cache/proxy_pool.json"):
        self.cache_path = cache_path
        self.proxies = []
        os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)

    def scrape_proxies(self) -> list[str]:
        """Scrapes free HTTP/HTTPS proxies from both sites."""
        urls = [
            "https://free-proxy-list.net/",
            "https://www.sslproxies.org/"
        ]
        scraped = set()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    html = response.read().decode('utf-8')
                soup = BeautifulSoup(html, "html.parser")

                # Check textarea first (raw list)
                textarea = soup.find("textarea")
                if textarea:
                    text_content = textarea.text
                    matches = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', text_content)
                    for m in matches:
                        scraped.add(m)

                # Table fallback
                table = soup.find("table")
                if table:
                    for row in table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) and port.isdigit():
                                scraped.add(f"{ip}:{port}")
            except Exception as e:
                logger.error(f"[ProxyManager] Error scraping {url}: {e}")

        return list(scraped)

    def load_pool(self) -> None:
        """Loads proxies from cache, or scrapes if cache is older than 1 hour / empty."""
        need_scrape = True
        if os.path.exists(self.cache_path):
            mtime = os.path.getmtime(self.cache_path)
            if time.time() - mtime < 3600:
                try:
                    with open(self.cache_path, encoding="utf-8") as f:
                        self.proxies = json.load(f)
                    if self.proxies:
                        need_scrape = False
                        logger.info(f"[ProxyManager] Loaded {len(self.proxies)} proxies from cache")
                except Exception as e:
                    logger.error(f"[ProxyManager] Failed to read proxy cache: {e}")

        if need_scrape:
            logger.info("[ProxyManager] Scraping fresh proxy list...")
            self.proxies = self.scrape_proxies()
            try:
                with open(self.cache_path, "w", encoding="utf-8") as f:
                    json.dump(self.proxies, f, indent=2)
                logger.info(f"[ProxyManager] Scraped and cached {len(self.proxies)} proxies")
            except Exception as e:
                logger.error(f"[ProxyManager] Failed to write proxy cache: {e}")

    def validate_proxy(self, proxy: str) -> bool:
        """Lightweight validation of proxy to ensure connectivity."""
        try:
            proxy_support = urllib.request.ProxyHandler({'http': f"http://{proxy}", 'https': f"http://{proxy}"})
            opener = urllib.request.build_opener(proxy_support)
            req = urllib.request.Request("http://httpbin.org/ip", headers={"User-Agent": "Mozilla/5.0"})
            with opener.open(req, timeout=3) as resp:
                if resp.getcode() == 200:
                    return True
        except Exception:
            pass
        return False

    def get_proxy(self) -> str | None:
        """Returns a valid rotated proxy from the pool."""
        self.load_pool()
        if not self.proxies:
            return None

        candidates = list(self.proxies)
        random.shuffle(candidates)
        for checked_count, proxy in enumerate(candidates):
            if checked_count >= 5:
                logger.info("[ProxyManager] Reached validation limit of 5 proxies, stopping search.")
                break
            if self.validate_proxy(proxy):
                logger.info(f"[ProxyManager] Selected valid proxy: {proxy}")
                return proxy
            else:
                self.evict_proxy(proxy)
        return None

    def evict_proxy(self, proxy: str) -> None:
        """Evicts a failed proxy from the pool and saves to cache."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            try:
                with open(self.cache_path, "w", encoding="utf-8") as f:
                    json.dump(self.proxies, f, indent=2)
                logger.info(f"[ProxyManager] Evicted failed proxy {proxy} from pool")
            except Exception as e:
                logger.error(f"[ProxyManager] Failed to update proxy cache: {e}")


def _get_db():
    """Lazily import and return the DB connection factory from web.app_v2.

    Raises:
        ImportError: If web.app_v2 is unavailable in the current environment.
    """
    from web.app_v2 import get_db  # noqa: PLC0415 — intentional lazy import
    return get_db()


class GhostHunter:
    """
    Cloud-Native Autonomous Scraper.
    Uses DDGS to find LinkedIn jobs without IP bans.
    Uses Camoufox to scrape the public job descriptions.
    """

    def __init__(self):
        pass

    def hunt_for_user(
        self, user_id: str, job_title: str, location: str, max_jobs: int = 5
    ) -> None:
        """Scrape LinkedIn job postings for a user using DDGS + Camoufox.

        Args:
            user_id: The target user's identifier in the local DB.
            job_title: The job title to search for (e.g. 'Network Engineer').
            location: The target location string (e.g. 'Remote', 'Dubai').
            max_jobs: Maximum number of unique job URLs to process.
        """
        logger.info(f"[DATASET-FETCHER] Starting extraction for node {user_id}")
        query = f'site:linkedin.com/jobs/view/ "{job_title}" "{location}"'
        urls = []

        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_jobs * 2)
                for r in results:
                    if "linkedin.com/jobs/view/" in r.get("href", ""):
                        urls.append(r["href"])
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] DDGS Error: {e}")
            return

        if not urls:
            logger.info("[DATASET-FETCHER] No data points found for query")
            return

        urls = list(set(urls))[:max_jobs]

        # Check duplicate job URLs before spawning the browser process to save memory
        filtered_urls = []
        try:
            conn = _get_db()
            for url in urls:
                existing = conn.execute(
                    "SELECT 1 FROM jobs WHERE user_id = ? AND url = ?",
                    (user_id, url),
                ).fetchone()
                if not existing:
                    filtered_urls.append(url)
            conn.close()
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Error filtering duplicates: {e}")
            filtered_urls = list(urls)

        if not filtered_urls:
            logger.info("[DATASET-FETCHER] All found URLs are duplicates. Skipping browser launch.")
            return

        logger.info(
            f"[DATASET-FETCHER] Found {len(filtered_urls)} new data URLs. Extracting features..."
        )

        proxy_manager = ProxyManager()
        proxy = proxy_manager.get_proxy()

        launch_kwargs = {"headless": True}
        if proxy:
            launch_kwargs["proxy"] = {"server": f"http://{proxy}"}
            logger.info(f"[DATASET-FETCHER] Using proxy: {proxy}")

        # For Camoufox, we run it synchronously since it's blocking
        try:
            from camoufox.sync_api import Camoufox

            with Camoufox(**launch_kwargs) as browser:
                page = browser.new_page()
                for url in filtered_urls:
                    try:
                        logger.info(f"[DATASET-FETCHER] Fetching page: {url}")
                        page.goto(url, timeout=30000)
                        time.sleep(random.uniform(2, 4))  # Human delay
                        html = page.content()

                        soup = BeautifulSoup(html, "html.parser")
                        title_elem = soup.find("h1")
                        title = (
                            title_elem.text.strip() if title_elem else "Unknown Title"
                        )

                        company_elem = soup.find(
                            "a", {"class": "topcard__org-name-link"}
                        )
                        company = (
                            company_elem.text.strip()
                            if company_elem
                            else "Unknown Company"
                        )

                        desc_elem = soup.find("div", {"class": "description__text"})
                        desc = desc_elem.text.strip() if desc_elem else ""

                        if len(desc) > 50:
                            job_id = (
                                f"gh_{int(time.time())}_{random.randint(1000, 9999)}"
                            )
                            conn = _get_db()
                            conn.execute(
                                """
                                INSERT INTO jobs (job_id, user_id, title, company, description, url, source, status)
                                VALUES (?, ?, ?, ?, ?, ?, 'ghost_hunter', 'new')
                            """,
                                (job_id, user_id, title, company, desc, url),
                            )
                            if hasattr(conn, "commit"):
                                conn.commit()
                            conn.close()
                            logger.info(
                                f"[DATASET-FETCHER] Ingested sample: {title} at {company}"
                            )

                        # ANTI-BAN JITTER: Randomized delay from 15 to 35 seconds to avoid HF bot detection
                        jitter = random.uniform(15, 35)
                        logger.info(
                            f"[DATASET-FETCHER] Applying network backoff ({jitter:.1f}s)"
                        )
                        time.sleep(jitter)

                    except Exception as e:
                        err_str = str(e).lower()
                        if "connection" in err_str or "proxy" in err_str or "timeout" in err_str or "net::err_" in err_str:
                            logger.error(f"[DATASET-FETCHER] Proxy error or connection issue processing {url}: {e}")
                            if proxy:
                                proxy_manager.evict_proxy(proxy)
                        else:
                            logger.error(f"[DATASET-FETCHER] Error processing {url}: {e}")
        except ImportError:
            logger.error("[DATASET-FETCHER] Headless dependency not installed.")
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Runtime Error: {e}")
            err_str = str(e).lower()
            if "connection" in err_str or "proxy" in err_str or "timeout" in err_str or "net::err_" in err_str:
                if proxy:
                    proxy_manager.evict_proxy(proxy)

    def run_all_users(self):
        """Finds all active users and hunts for their target roles"""
        try:
            conn = _get_db()
            users = conn.execute(
                "SELECT user_id, cv_text FROM users WHERE cv_text IS NOT NULL"
            ).fetchall()
            conn.close()

            for user in users:
                user_id = user["user_id"]
                target_role = "Software Engineer"
                location = "Remote"
                self.hunt_for_user(user_id, target_role, location, max_jobs=2)
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Global run error: {e}")


if __name__ == "__main__":
    hunter = GhostHunter()
    hunter.run_all_users()

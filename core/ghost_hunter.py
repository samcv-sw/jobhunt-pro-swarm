import time
import random
from loguru import logger
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from web.app_v2 import get_db


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
    ):
        logger.info(f"[DATASET-FETCHER] Starting extraction for node {user_id}")
        query = f'site:linkedin.com/jobs/view/ "{job_title}" "{location}"'
        urls = []

        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_jobs * 2)
                for r in results:
                    if "linkedin.com/jobs/view/" in r.get("href", ""):
                        urls.append(r["href"])
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] DDGS Error: {e}")
            return

        if not urls:
            logger.info(f"[DATASET-FETCHER] No data points found for query")
            return

        urls = list(set(urls))[:max_jobs]
        logger.info(
            f"[DATASET-FETCHER] Found {len(urls)} data URLs. Extracting features..."
        )

        # For Camoufox, we run it synchronously since it's blocking
        try:
            from camoufox.sync_api import Camoufox

            with Camoufox(headless=True) as browser:
                page = browser.new_page()
                for url in urls:
                    try:
                        # Check if job already exists for this user
                        conn = get_db()
                        conn.cursor() if hasattr(conn, "cursor") else conn
                        existing = conn.execute(
                            "SELECT 1 FROM jobs WHERE user_id = ? AND url = ?",
                            (user_id, url),
                        ).fetchone()
                        if existing:
                            conn.close()
                            continue

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
                            conn.execute(
                                """
                                INSERT INTO jobs (job_id, user_id, title, company, description, url, source, status)
                                VALUES (?, ?, ?, ?, ?, ?, 'ghost_hunter', 'new')
                            """,
                                (job_id, user_id, title, company, desc, url),
                            )
                            if hasattr(conn, "commit"):
                                conn.commit()
                            logger.info(
                                f"[DATASET-FETCHER] Ingested sample: {title} at {company}"
                            )

                        conn.close()

                        # ANTI-BAN JITTER: Randomized delay from 15 to 35 seconds to avoid HF bot detection
                        jitter = random.uniform(15, 35)
                        logger.info(
                            f"[DATASET-FETCHER] Applying network backoff ({jitter:.1f}s)"
                        )
                        time.sleep(jitter)

                    except Exception as e:
                        logger.error(f"[DATASET-FETCHER] Error processing {url}: {e}")
        except ImportError:
            logger.error("[DATASET-FETCHER] Headless dependency not installed.")
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Runtime Error: {e}")

    def run_all_users(self):
        """Finds all active users and hunts for their target roles"""
        try:
            conn = get_db()
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

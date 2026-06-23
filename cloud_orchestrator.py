import asyncio
import logging
import sys
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

# ── Cloud-Only Orchestrator ──
# This runs on PythonAnywhere (triggered by GH Actions cron).
# NO local PC required. NO local files. Everything in DB + APIs.

import config
from core.database import Database
from core.job_search import MultiSourceSearch
from core.email_engine import EmailEngine
from core.cover_letter import CoverLetterWriter
from core.analytics import Analytics
from core.smart_scheduler import SmartScheduler
from core.anti_ban import anti_ban
from core.personalizer import personalizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [CLOUD-ORCH] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class CloudOrchestrator:
    """
    Cloud-only orchestrator — runs from PA via GH Actions cron tick.
    No PC, no local storage, no file dependencies.
    """

    def __init__(self):
        self.db = Database()
        self.search = MultiSourceSearch()
        self.email = EmailEngine()
        self.scheduler = SmartScheduler()
        self.analytics = Analytics()

    async def tick(self) -> Dict:
        """
        Lightweight tick — called every 30 min by GH Actions cron.
        Returns status dict for the cron response.
        """
        logger.info("=" * 50)
        logger.info("  CLOUD TICK v2 — Zero PC Mode")
        logger.info("=" * 50)

        results = {
            "timestamp": datetime.now().isoformat(),
            "health": {},
            "campaigns": 0,
            "jobs_found": 0,
            "emails_sent": 0,
            "revenue": 0.0,
            "status": "ok"
        }

        # ── Phase 1: Health check ──
        try:
            db_ok = await self.db.ping() if hasattr(self.db, 'ping') else True
            results["health"] = {"db": db_ok, "ai": self._check_ai(), "smtp": self._check_smtp()}
        except Exception as e:
            logger.warning(f"Health check: {e}")

        # ── Phase 2: Resume pending campaigns ──
        try:
            campaigns = await self._resume_campaigns()
            results["campaigns"] = len(campaigns)
            for c in campaigns:
                logger.info(f"  Campaign {c}: processed")
        except Exception as e:
            logger.warning(f"Campaign resume: {e}")

        # ── Phase 3: Scrape jobs using PA-approved scraper (JSearch + LinkedIn XHR) ──
        try:
            from core.pa_job_scraper import PAJobScraper
            pa_scraper = PAJobScraper()
            jobs = pa_scraper.search_all(max_jobs=50)
            results["jobs_found"] = len(jobs)
            logger.info(f"PA scraper found {len(jobs)} jobs")
            
            # Store jobs in DB for campaign processing
            if jobs:
                try:
                    db_path = self._get_db_path()
                    conn = sqlite3.connect(db_path, timeout=30)
                    for j in jobs:
                        try:
                            conn.execute(
                                "INSERT INTO jobs (title, company, location, url, source, email, snippet, status) VALUES (?,?,?,?,?,?,?,'new')",
                                (j.get('title',''), j.get('company',''), j.get('location',''),
                                 j.get('url',''), j.get('source','jsearch'), j.get('email',''), j.get('snippet',''))
                            )
                        except Exception:
                            pass
                    conn.commit()
                    conn.close()
                except Exception as dbe:
                    logger.warning(f"Store jobs in DB: {dbe}")
        except Exception as e:
            logger.warning(f"PA scraper error: {e}")

        # ── Phase 4: Send queued emails ──
        try:
            sent = await self._drain_email_queue(max_emails=50)
            results["emails_sent"] = sent
        except Exception as e:
            logger.warning(f"Email drain: {e}")

        # ── Phase 5: Revenue check ──
        try:
            stats = self.analytics.get_stats()
            results["revenue"] = stats.get("revenue_total", 0)
        except Exception as e:
            logger.warning(f"Revenue: {e}")

        # ── Report ──
        try:
            await self._telegram_summary(results)
        except Exception:
            pass

        logger.info("  Cloud tick complete: %s", results)
        return results

    def _check_ai(self) -> bool:
        """Check if Groq API key is available."""
        return bool(os.getenv("GROQ_API_KEY", "") or getattr(config, "GROQ_API_KEY", ""))

    def _check_smtp(self) -> bool:
        """Check if at least one SMTP account is configured."""
        return bool(
            os.getenv("BREVO_API_KEY", "") or
            os.getenv("GMAIL1_USER", "")
        )

    async def _resume_campaigns(self) -> List[str]:
        """Resume any pending/running campaigns.
        Also reprocess campaigns that are stuck (completed but 0 emails sent).
        """
        import sqlite3
        db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
        if not db_path or not os.path.exists(db_path):
            base = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base, "jobhunt_saas_v2.db")
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            conn.row_factory = sqlite3.Row

            # Active campaigns to process
            active = conn.execute(
                "SELECT campaign_id FROM campaigns WHERE status IN ('pending', 'running')"
            ).fetchall()

            # Stuck campaigns: completed but with 0 sent emails
            stuck = conn.execute("""
                SELECT c.campaign_id
                FROM campaigns c
                LEFT JOIN campaign_emails ce ON c.campaign_id = ce.campaign_id AND ce.status = 'sent'
                WHERE c.status = 'completed'
                GROUP BY c.campaign_id
                HAVING COUNT(ce.id) = 0
                UNION ALL
                SELECT c.campaign_id
                FROM campaigns c
                WHERE c.status = 'completed'
                AND c.sent_count = 0
                AND c.total_companies > 0
            """).fetchall()

            all_campaigns = list(active) + list(stuck)
            conn.close()

            # PA FREE TIER LIMIT: process at most 2 campaigns per tick
            # Each campaign takes 60-120s on PA. Web requests have 250s timeout.
            # Processing more will crash PA and waste the remaining campaigns.
            max_per_tick = 2
            results = []
            for idx, row in enumerate(all_campaigns):
                if idx >= max_per_tick:
                    logger.info(f"  PA budget: processed {max_per_tick}, leaving rest for next tick")
                    break
                cid = row["campaign_id"]
                try:
                    from core.campaign_runner import run_campaign
                    await run_campaign(cid, lambda db=db_path: sqlite3.connect(db, timeout=30, check_same_thread=False), config)
                    results.append(cid)
                    logger.info(f"  Campaign {cid} processed")
                except Exception as e:
                    logger.error(f"Campaign {cid} failed: {e}")
            return results
        except Exception as e:
            logger.error(f"DB error: {e}")
            return []

    def _get_db_path(self) -> str:
        """Get the database file path."""
        db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
        if not os.path.exists(db_path):
            base = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base, "jobhunt_saas_v2.db")
        if not os.path.exists(db_path):
            db_path = os.path.join(os.getcwd(), "jobhunt_saas_v2.db")
        return db_path

    async def _drain_email_queue(self, max_emails: int = 50) -> int:
        """Send pending emails from the email_queue table."""
        sent = 0
        try:
            engine = EmailEngine()
            queue = engine.get_queue(limit=max_emails)
            if not queue:
                logger.info(f"  No pending emails in queue (checked {max_emails})")
                return 0
            logger.info(f"  Found {len(queue)} emails in queue")
            for item in queue:
                try:
                    success = await engine.send_from_queue_item(item)
                    if success:
                        sent += 1
                        # Mark as sent
                        import sqlite3, os
                        db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
                        if not os.path.exists(db_path):
                            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobhunt_saas_v2.db")
                        try:
                            qid = item.get("id")
                            if qid:
                                conn = sqlite3.connect(db_path, timeout=10)
                                conn.execute("UPDATE email_queue SET status='sent', sent_at=CURRENT_TIMESTAMP WHERE id=?", (qid,))
                                conn.commit()
                                conn.close()
                        except Exception:
                            pass
                    await asyncio.sleep(2)  # Rate limit between queue emails
                except Exception as e:
                    logger.warning(f"Queue item failed: {e}")
        except Exception as e:
            logger.warning(f"Drain queue: {e}")
        return sent

    async def _telegram_summary(self, results: Dict):
        """Send a quick summary to Telegram."""
        try:
            from core.telegram_bot import send_telegram_message_sync
            h = results["health"]
            msg = (
                f"🤖 Cloud Tick\n"
                f"Campaigns: {results['campaigns']}\n"
                f"Jobs: {results['jobs_found']}\n"
                f"Emails: {results['emails_sent']}\n"
                f"DB: {'✅' if h.get('db') else '❌'}\n"
                f"AI: {'✅' if h.get('ai') else '❌'}\n"
                f"SMTP: {'✅' if h.get('smtp') else '❌'}\n"
                f"Rev: ${results['revenue']:.0f}"
            )
            send_telegram_message_sync(msg)
        except Exception:
            pass


async def cloud_tick() -> Dict:
    """
    Single tick for GH Actions cron trigger.
    Returns JSON-serializable dict.
    """
    orch = CloudOrchestrator()
    return await orch.tick()


if __name__ == "__main__":
    result = asyncio.run(cloud_tick())
    print(json.dumps(result))

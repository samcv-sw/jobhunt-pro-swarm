import asyncio
import logging
import sys
import os
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

        # ── Phase 3: Scrape jobs (if capacity) ──
        try:
            jobs = await self.search.search_all(max_results=20)
            results["jobs_found"] = len(jobs)
        except Exception as e:
            logger.warning(f"Search: {e}")

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
        """Resume any pending/running campaigns."""
        import sqlite3
        db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            conn.row_factory = sqlite3.Row
            active = conn.execute(
                "SELECT campaign_id FROM campaigns WHERE status IN ('pending', 'running')"
            ).fetchall()
            conn.close()

            results = []
            for row in active:
                cid = row["campaign_id"]
                try:
                    from core.campaign_runner import run_campaign
                    await run_campaign(cid, lambda: sqlite3.connect(db_path, timeout=30), config)
                    results.append(cid)
                except Exception as e:
                    logger.error(f"Campaign {cid} failed: {e}")
            return results
        except Exception as e:
            logger.error(f"DB error: {e}")
            return []

    async def _drain_email_queue(self, max_emails: int = 50) -> int:
        """Send pending emails from the queue."""
        sent = 0
        try:
            from core.email_engine import EmailEngine
            engine = EmailEngine()
            # Get queued emails
            queue = engine.get_queue(limit=max_emails) if hasattr(engine, 'get_queue') else []
            for item in queue[:max_emails]:
                try:
                    engine.send_sync(
                        to=item.get("to", ""),
                        subject=item.get("subject", ""),
                        body=item.get("body", ""),
                    )
                    sent += 1
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

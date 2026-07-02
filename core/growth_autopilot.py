"""
JobHunt Pro - Autonomous Growth Engine Autopilot
Injects AI automated client acquisition tasks into the Job Queue.
Runs continuously in the background on the web server.
"""

import logging
import threading
import time
from datetime import datetime
from core.job_queue import enqueue_task

logger = logging.getLogger(__name__)

# Track last execution to prevent flooding the queue
_last_run = {
    "seo": None,
    "b2b": None,
    "social": None,
    "viral_video": None,
    "influencer": None,
}


def _autopilot_loop():
    while True:
        now = datetime.now()

        # 1. SEO Auto-Blogging (Runs once every 24 hours)
        if _last_run["seo"] is None or (now - _last_run["seo"]).total_seconds() > 86400:
            logger.info("[AUTOPILOT] Injecting AI SEO Task...")
            enqueue_task(
                "growth_seo",
                {"topic": "Automated Job Applications in 2026", "length": "1500_words"},
            )
            _last_run["seo"] = now

        # 2. B2B Cold Outreach (Runs once every 12 hours)
        if _last_run["b2b"] is None or (now - _last_run["b2b"]).total_seconds() > 43200:
            logger.info("[AUTOPILOT] Injecting B2B HR Outreach Task...")
            enqueue_task(
                "growth_b2b",
                {"target": "hr_directors", "pitch": "hr_automation_package"},
            )
            _last_run["b2b"] = now

        # 3. Social AI Sniper (Runs once every 6 hours)
        if (
            _last_run["social"] is None
            or (now - _last_run["social"]).total_seconds() > 21600
        ):
            logger.info("[AUTOPILOT] Injecting Social Media AI Sniper Task...")
            enqueue_task(
                "growth_social",
                {"platform": "reddit_twitter", "mode": "empathetic_pitch"},
            )
            _last_run["social"] = now

        # 4. Viral TikTok/Reels Generator (Runs once every 24 hours to generate 5 videos)
        if (
            _last_run["viral_video"] is None
            or (now - _last_run["viral_video"]).total_seconds() > 86400
        ):
            logger.info("[AUTOPILOT] Injecting Viral Video Factory Task...")
            enqueue_task("growth_viral_video", {"count": 5})
            _last_run["viral_video"] = now

        # 5. Influencer Affiliate Outreach (Runs once every 24 hours)
        if (
            _last_run["influencer"] is None
            or (now - _last_run["influencer"]).total_seconds() > 86400
        ):
            logger.info("[AUTOPILOT] Injecting Influencer Outreach Task...")
            enqueue_task("growth_influencer", {"platform": "youtube_tiktok"})
            _last_run["influencer"] = now

        # Sleep for 1 hour before checking again
        time.sleep(3600)


def start_autopilot():
    """Starts the background thread that continuously schedules AI growth tasks."""
    t = threading.Thread(target=_autopilot_loop, daemon=True)
    t.start()
    logger.info(
        "[AUTOPILOT] AI Growth Engine Started! Clients will now be acquired automatically."
    )

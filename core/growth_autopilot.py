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


def _autopilot_loop() -> None:
    while True:
        try:
            now = datetime.now()

            # 1. SEO Auto-Blogging (Runs once every 24 hours)
            if _last_run["seo"] is None or (now - _last_run["seo"]).total_seconds() > 86400:
                logger.info("[AUTOPILOT] Injecting AI SEO Task...")
                try:
                    enqueue_task(
                        "growth_seo",
                        {"topic": "Automated Job Applications in 2026", "length": "1500_words"},
                    )
                    _last_run["seo"] = now
                except Exception as e:
                    logger.error("[AUTOPILOT] Failed to enqueue SEO task: %s", e)

            # 2. B2B Cold Outreach (Runs once every 12 hours)
            if _last_run["b2b"] is None or (now - _last_run["b2b"]).total_seconds() > 43200:
                logger.info("[AUTOPILOT] Injecting B2B HR Outreach Task...")
                try:
                    enqueue_task(
                        "growth_b2b",
                        {"target": "hr_directors", "pitch": "hr_automation_package"},
                    )
                    _last_run["b2b"] = now
                except Exception as e:
                    logger.error("[AUTOPILOT] Failed to enqueue B2B outreach task: %s", e)

            # 3. Social AI Sniper (Runs once every 6 hours)
            if (
                _last_run["social"] is None
                or (now - _last_run["social"]).total_seconds() > 21600
            ):
                logger.info("[AUTOPILOT] Injecting Social Media AI Sniper Task...")
                try:
                    enqueue_task(
                        "growth_social",
                        {"platform": "reddit_twitter", "mode": "empathetic_pitch"},
                    )
                    _last_run["social"] = now
                except Exception as e:
                    logger.error("[AUTOPILOT] Failed to enqueue Social Sniper task: %s", e)

            # 4. Viral TikTok/Reels Generator (Runs once every 24 hours to generate 5 videos)
            if (
                _last_run["viral_video"] is None
                or (now - _last_run["viral_video"]).total_seconds() > 86400
            ):
                logger.info("[AUTOPILOT] Injecting Viral Video Factory Task...")
                try:
                    enqueue_task("growth_viral_video", {"count": 5})
                    _last_run["viral_video"] = now
                except Exception as e:
                    logger.error("[AUTOPILOT] Failed to enqueue Viral Video task: %s", e)

            # 5. Influencer Affiliate Outreach (Runs once every 24 hours)
            if (
                _last_run["influencer"] is None
                or (now - _last_run["influencer"]).total_seconds() > 86400
            ):
                logger.info("[AUTOPILOT] Injecting Influencer Outreach Task...")
                try:
                    enqueue_task("growth_influencer", {"platform": "youtube_tiktok"})
                    _last_run["influencer"] = now
                except Exception as e:
                    logger.error("[AUTOPILOT] Failed to enqueue Influencer Outreach task: %s", e)
        except Exception as e:
            logger.error("[AUTOPILOT] Unexpected fatal loop error: %s", e, exc_info=True)

        # Sleep for 1 hour before checking again
        time.sleep(3600)


def trigger_apex_growth_burst() -> dict:
    """Triggers an immediate multi-channel AI growth burst across all 5 acquisition channels."""
    from core.client_hunter import client_hunter_engine
    
    # 1. B2B Global Scan & Pitch
    b2b_cycle = client_hunter_engine.run_full_acquisition_cycle(region="GCC")
    
    # 2. Enqueue SEO, Social, Video & Influencer Tasks
    tasks_triggered = []
    try:
        enqueue_task("growth_seo", {"topic": "AI Resume & Autonomous Applications 2026", "length": "1500_words"})
        tasks_triggered.append("growth_seo")
        enqueue_task("growth_b2b", {"target": "global_hr_directors", "pitch": "apex_white_label"})
        tasks_triggered.append("growth_b2b")
        enqueue_task("growth_social", {"platform": "x_linkedin_reddit", "mode": "viral_case_study"})
        tasks_triggered.append("growth_social")
        enqueue_task("growth_viral_video", {"count": 5})
        tasks_triggered.append("growth_viral_video")
        enqueue_task("growth_influencer", {"platform": "global_creator_network"})
        tasks_triggered.append("growth_influencer")
    except Exception as e:
        logger.warning(f"[AUTOPILOT] Burst enqueue notice: {e}")

    return {
        "status": "success",
        "burst_mode": "APEX_MAXIMUM_GLOBAL",
        "channels_activated": len(tasks_triggered) + 1,
        "tasks_enqueued": tasks_triggered,
        "b2b_acquisition_telemetry": b2b_cycle["telemetry"]
    }

def start_autopilot() -> None:
    """Starts the background thread that continuously schedules AI growth tasks."""
    try:
        t = threading.Thread(target=_autopilot_loop, daemon=True)
        t.start()
        logger.info(
            "[AUTOPILOT] AI Growth Engine Started! Clients will now be acquired automatically."
        )
    except Exception as e:
        logger.error("[AUTOPILOT] Failed to start autopilot thread: %s", e, exc_info=True)


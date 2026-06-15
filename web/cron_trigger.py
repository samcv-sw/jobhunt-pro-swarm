"""
JobHunt Pro - PythonAnywhere Cron Trigger
=============================================
Standalone script for PA Scheduled Tasks.

Called every 30 minutes by PA cron:
    python /home/jhfguf/jobhunt/web/cron_trigger.py

Runs the full job cycle: Search → Apply → Follow-up
PLUS daily database backup (once per day at first run after midnight UTC).
"""
import sys
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - PA-CRON - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(_PROJECT_ROOT / "logs" / "cron_trigger.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("cron_trigger")

# ── Backup state file ───────────────────────────────────────
_BACKUP_STATE_FILE = _PROJECT_ROOT / "logs" / "last_backup_date.txt"


def _should_run_backup() -> bool:
    """Check if a backup should run now (once per day, UTC-based)."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        if _BACKUP_STATE_FILE.exists():
            last_date = _BACKUP_STATE_FILE.read_text().strip()
            if last_date == today_str:
                return False
    except Exception:
        pass
    return True


def _mark_backup_done():
    """Record that we ran backup today."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _BACKUP_STATE_FILE.write_text(today_str)


def run_daily_backup():
    """Run database backup via core/auto_backup.py — synchronous, safe for PA."""
    try:
        from core.auto_backup import run_backup

        logger.info("=" * 40)
        logger.info("  DAILY BACKUP — Starting")
        logger.info("=" * 40)

        result = run_backup()

        if result["success"]:
            logger.info(
                "✅ Daily backup OK: %s (%.1f MB, %.1fs) telegram=%s",
                Path(result.get("backup_path", "")).name if result.get("backup_path") else "?",
                result.get("db_size_mb", 0),
                result.get("duration_s", 0),
                result.get("telegram_sent", False),
            )
        else:
            logger.error("❌ Daily backup FAILED: %s", result.get("error", "unknown"))

        _mark_backup_done()
        return result

    except ImportError as e:
        logger.warning("auto_backup module not available: %s", e)
    except Exception as e:
        logger.exception("Daily backup error: %s", e)
    return None


async def run_cycle():
    """Run one full job-hunt cycle."""
    from orchestrator import Orchestrator

    orch = Orchestrator()
    logger.info("=" * 60)
    logger.info("  PA CRON — Starting Job Cycle")
    logger.info("=" * 60)

    result = await orch.run_full_cycle()

    logger.info("=" * 60)
    logger.info("  PA CRON — Cycle Complete")
    logger.info(f"  Found:    {result['found']}")
    logger.info(f"  Applied:  {result['applied']}")
    logger.info(f"  Followups:{result['followups']}")
    logger.info("=" * 60)
    return result


def main():
    """Synchronous entry point for PA cron (runs async internally).

    Executes:
      1. Daily database backup (only first run after midnight UTC)
      2. Full job cycle (Search → Apply → Follow-up)
    """
    logger.info("PA Cron Trigger started")

    # ── Daily backup (runs once per UTC day) ───────────────
    if _should_run_backup():
        logger.info("📦 Daily backup window — running backup before job cycle")
        run_daily_backup()
    else:
        logger.info("📦 Backup already done today — skipping")

    # ── Job cycle ──────────────────────────────────────────
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_cycle())
        loop.close()
        logger.info("PA Cron Trigger completed successfully")

        # Write status marker
        marker_path = _PROJECT_ROOT / "logs" / "cron_last_run.txt"
        marker_path.write_text(
            f"Last run: {datetime.now(timezone.utc).isoformat()} | "
            f"Found: {result['found']}, Applied: {result['applied']}, "
            f"Followups: {result['followups']}\n"
        )
        return 0

    except Exception as e:
        logger.exception("PA Cron Trigger FAILED: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
JobHunt Pro - Automated Database Backup System
================================================
Backs up jobhunt_saas_v2.db every 6 hours using SQLite's native .backup() API.
Sends compressed backup to Telegram as a document.
Keeps last 5 backups, rotates older ones.
Logs all operations to logs/backup.log.

Designed for PythonAnywhere free tier (≈5 min task timeout) —
backup completes in <30s even for 100MB+ databases.

Usage:
    python core/auto_backup.py              # Run once (manual)
    python core/auto_backup.py --daemon     # Run every 6h (for cloud entrypoints)

Env vars required:
    TELEGRAM_BOT_TOKEN  - Telegram bot token
    TELEGRAM_CHAT_ID    - Telegram chat/group ID to send backups to
    DB_PATH (optional)  - Path to SQLite DB (default: jobhunt_saas_v2.db)
"""

import os
import sys
import gzip
import shutil
import sqlite3
import logging
import argparse
import time as _time
from datetime import datetime, timezone
from pathlib import Path

# ── Project root ────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ── Ensure dirs exist ───────────────────────────────────────
for _d in ["data", "logs"]:
    (ROOT_DIR / _d).mkdir(parents=True, exist_ok=True)
(ROOT_DIR / "data" / "backups").mkdir(parents=True, exist_ok=True)

# ── Logging ─────────────────────────────────────────────────
LOG_FILE = ROOT_DIR / "logs" / "backup.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - BACKUP - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
logger = logging.getLogger("auto_backup")

# ── Config ──────────────────────────────────────────────────
BACKUP_DIR = ROOT_DIR / "data" / "backups"
MAX_BACKUPS = 5
DB_NAME = "jobhunt_saas_v2.db"
DB_PATH = ROOT_DIR / DB_NAME

# Fallback: check data/ subdirectory
if not DB_PATH.exists():
    alt = ROOT_DIR / "data" / DB_NAME
    if alt.exists():
        DB_PATH = alt


def _load_env():
    """Load .env if not already loaded (safe for re-entry)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT_DIR / ".env")
    except ImportError:
        pass


def _get_db_size_mb(path: Path) -> float:
    """Return database file size in MB."""
    if path.exists():
        return path.stat().st_size / (1024 * 1024)
    return 0.0


def _rotate_backups():
    """Keep only the last MAX_BACKUPS files in BACKUP_DIR (by mtime)."""
    files = sorted(
        BACKUP_DIR.glob("jobhunt_saas_v2_*.db.gz"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if len(files) > MAX_BACKUPS:
        for old in files[MAX_BACKUPS:]:
            try:
                old.unlink()
                logger.info("Rotated out old backup: %s", old.name)
            except OSError as e:
                logger.warning("Failed to rotate %s: %s", old.name, e)


def backup_database() -> str | None:
    """Perform a native SQLite .backup() to a compressed file.

    Uses sqlite3.Connection.backup() which is:
      - Atomic (all-or-nothing via the backup API)
      - Lock-safe (acquires a shared lock, doesn't block reads)
      - Fast (binary copy, not row-by-row export)

    Returns:
        Path to the compressed backup file, or None on failure.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"jobhunt_saas_v2_{timestamp}.db.gz"
    backup_path = BACKUP_DIR / backup_name
    temp_db_path = BACKUP_DIR / f"_temp_backup_{timestamp}.db"

    if not DB_PATH.exists():
        logger.error("Database not found at: %s", DB_PATH)
        return None

    db_size_mb = _get_db_size_mb(DB_PATH)
    logger.info(
        "Starting backup: %s (%.2f MB) -> %s",
        DB_NAME,
        db_size_mb,
        backup_name,
    )

    t_start = _time.monotonic()

    try:
        # Step 1: SQLite native backup to temp file (atomic, lock-safe)
        src = sqlite3.connect(str(DB_PATH))
        dst = sqlite3.connect(str(temp_db_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        logger.debug("SQLite .backup() complete in %.1fs", _time.monotonic() - t_start)

        # Step 2: Gzip compress
        _time.monotonic()
        with open(temp_db_path, "rb") as f_in:
            with gzip.open(str(backup_path), "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out, length=1024 * 1024)
        compressed_size_mb = backup_path.stat().st_size / (1024 * 1024)
        elapsed = _time.monotonic() - t_start
        logger.info(
            "Backup complete: %s (%.2f MB -> %.2f MB compressed, %.1fs)",
            backup_name,
            db_size_mb,
            compressed_size_mb,
            elapsed,
        )
        return str(backup_path)

    except sqlite3.OperationalError as e:
        logger.error("SQLite backup failed (db locked?): %s", e)
        return None
    except Exception as e:
        logger.exception("Backup failed: %s", e)
        return None
    finally:
        # Clean up temp file
        if temp_db_path.exists():
            try:
                temp_db_path.unlink()
            except OSError:
                pass


def send_to_telegram(filepath: str, caption: str = "") -> bool:
    """Send a file to Telegram as a document via bot API.

    Args:
        filepath: Path to the file to send.
        caption: Optional caption text.

    Returns:
        True if sent successfully, False otherwise.
    """
    _load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        logger.warning("Telegram not configured — skipping cloud backup")
        return False

    # Telegram has a 50MB file size limit for bots
    file_size_mb = Path(filepath).stat().st_size / (1024 * 1024)
    if file_size_mb > 49:
        logger.warning(
            "Backup too large for Telegram (%.1f MB > 50MB limit) — skipping send",
            file_size_mb,
        )
        return False

    try:
        import requests as _requests

        url = f"https://api.telegram.org/bot{token}/sendDocument"
        filename = Path(filepath).name

        with open(filepath, "rb") as f:
            response = _requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"document": (filename, f, "application/gzip")},
                timeout=120,
            )

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("ok"):
                logger.info("Backup sent to Telegram: %s", filename)
                return True
            else:
                logger.error(
                    "Telegram API error: %s", resp_json.get("description", "unknown")
                )
                return False
        else:
            logger.error(
                "Telegram HTTP %d: %s", response.status_code, response.text[:200]
            )
            return False

    except Exception as e:
        logger.exception("Failed to send backup to Telegram: %s", e)
        return False


def run_backup() -> dict:
    """Run a complete backup cycle: backup -> rotate -> send -> log.

    Returns:
        Dict with status info for logging/telemetry.
    """
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": False,
        "backup_path": None,
        "telegram_sent": False,
        "db_size_mb": 0.0,
        "duration_s": 0.0,
        "error": None,
    }

    t_start = _time.monotonic()

    try:
        # Step 1: Backup
        backup_path = backup_database()
        if not backup_path:
            result["error"] = "backup_creation_failed"
            return result

        result["backup_path"] = backup_path
        result["db_size_mb"] = _get_db_size_mb(DB_PATH)

        # Step 2: Rotate old backups
        _rotate_backups()

        # Step 3: Send to Telegram (cloud off-site backup)
        db_size_str = f"{result['db_size_mb']:.1f} MB"
        caption = (
            f"[DB] **JobHunt Pro DB Backup**\n"
            f"Date: {result['timestamp'][:19].replace('T', ' ')} UTC\n"
            f"Size: {db_size_str} -> {Path(backup_path).name}\n"
            f"Keep: Keeping last {MAX_BACKUPS} backups"
        )
        result["telegram_sent"] = send_to_telegram(backup_path, caption)
        result["success"] = True

    except Exception as e:
        logger.exception("Backup cycle failed: %s", e)
        result["error"] = str(e)[:500]

    finally:
        result["duration_s"] = round(_time.monotonic() - t_start, 2)
        logger.info(
            "Backup cycle: success=%s telegram=%s duration=%.1fs",
            result["success"],
            result["telegram_sent"],
            result["duration_s"],
        )

    return result


def run_backup_loop(interval_hours: int = 6):
    """Run backups on a timer. Designed for cloud entrypoints (run_cloud.py).

    Args:
        interval_hours: Hours between backups (default: 6).
    """
    logger.info(
        "Backup daemon started — interval=%dh, keep=%d",
        interval_hours,
        MAX_BACKUPS,
    )

    import signal as _signal
    import asyncio as _asyncio

    shutdown_flag = False

    def _handle_signal(signum, frame):
        nonlocal shutdown_flag
        logger.info("Backup daemon received signal %s — shutting down", signum)
        shutdown_flag = True

    _signal.signal(_signal.SIGTERM, _handle_signal)
    _signal.signal(_signal.SIGINT, _handle_signal)

    async def _loop():
        nonlocal shutdown_flag
        # Run first backup after a short delay (let web server start)
        await _asyncio.sleep(30)
        while not shutdown_flag:
            logger.info("── Backup cycle starting ──")
            run_backup()
            # Sleep in 1s increments so we can respond to shutdown quickly
            for _ in range(interval_hours * 3600):
                if shutdown_flag:
                    break
                await _asyncio.sleep(1)

    try:
        _asyncio.run(_loop())
    except KeyboardInterrupt:
        pass
    logger.info("Backup daemon stopped")


# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobHunt Pro Database Backup")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run backup daemon (every 6h)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Backup interval in hours (default: 6)",
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Skip Telegram upload (save locally only)",
    )
    args = parser.parse_args()

    _load_env()

    if args.daemon:
        run_backup_loop(interval_hours=args.interval)
    else:
        if args.no_telegram:
            # Override: just backup + rotate, no Telegram
            path = backup_database()
            if path:
                _rotate_backups()
                print(f"Local backup: {path}")
        else:
            result = run_backup()
            if result["success"]:
                print(f"✅ Backup complete: {result['backup_path']}")
                print(
                    f"   Telegram: {'sent' if result['telegram_sent'] else 'skipped'}"
                )
                print(f"   Duration: {result['duration_s']}s")
            else:
                print(f"❌ Backup failed: {result.get('error', 'unknown')}")
                sys.exit(1)

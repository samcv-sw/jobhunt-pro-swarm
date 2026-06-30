#!/usr/bin/env python3
"""
JobHunt Pro — Unified Cloud Entrypoint
========================================
Single-file launcher for ALL cloud platforms:
  - Render.com (free tier, recommended)
  - PythonAnywhere (expires June 20)
  - Railway.app (free tier, $5 credit)

What it does:
  1. Detects platform & auto-configures env
  2. Starts uvicorn with web.app_v2:app
  3. Runs database backup daemon (every 6h, sends to Telegram)
  4. Graceful shutdown on SIGTERM/SIGINT

Usage:
    python run_cloud.py              # Auto-detect platform
    python run_cloud.py --render     # Force Render mode
    python run_cloud.py --railway    # Force Railway mode
    python run_cloud.py --pa         # Force PA mode (synchronous)

No Docker needed. Works on free tiers.
"""
import os
import sys
import asyncio
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ── Project root ────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# ── Ensure required directories exist ───────────────────────
for _dir in ["data", "data/backups", "logs", "sent_mails", "cache"]:
    (ROOT_DIR / _dir).mkdir(parents=True, exist_ok=True)

# ── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            str(ROOT_DIR / "logs" / "cloud.log"), encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger("run_cloud")

# ── Global shutdown flag ────────────────────────────────────
_shutdown = False


# ═══════════════════════════════════════════════════════════════
# PLATFORM DETECTION
# ═══════════════════════════════════════════════════════════════

def detect_platform() -> str:
    """Auto-detect which cloud platform we're running on."""
    # Render.com
    if os.getenv("RENDER") or "render" in os.getenv("HOME", "").lower():
        return "render"
    # Railway
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_SERVICE_ID"):
        return "railway"
    # PythonAnywhere
    if (
        os.getenv("PYTHONANYWHERE_SITE")
        or os.getenv("PYTHONANYWHERE_DOMAIN")
        or "pythonanywhere" in os.getenv("HOME", "").lower()
    ):
        return "pa"
    # Local / unknown
    return "local"


def configure_platform(platform: str):
    """Set environment variables based on the detected platform."""
    logger.info("Platform: %s", platform.upper())

    # ── Port ──────────────────────────────────────────────
    port = os.getenv("PORT", "8000")
    os.environ["PORT"] = port

    # ── Database ──────────────────────────────────────────
    # Check if PostgreSQL URL is configured (Neon.tech, etc.)
    pg_url = (
        os.getenv("DATABASE_URL", "")
        or os.getenv("NEON_DATABASE_URL", "")
        or os.getenv("POSTGRES_URL", "")
    )
    is_postgres = pg_url.startswith("postgresql") or pg_url.startswith("postgres")

    if not is_postgres:
        logger.warning("No Postgres URL found, using default Neon DB for Project Omega")
        pg_url = "postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"
    
    # Use PostgreSQL (Neon.tech on any platform)
    logger.info("Database: PostgreSQL (Neon.tech)")
    os.environ["DATABASE_URL"] = pg_url
    sync_url = pg_url.replace("+asyncpg://", "://").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    os.environ["DATABASE_URL_SYNC"] = sync_url

    # ── DB_PATH for legacy code ──
    # Disabled for Project Omega
    os.environ["DB_PATH"] = ""

    # ── Cloud mode ────────────────────────────────────────
    os.environ["CLOUD_MODE"] = "true"

    # ── Platform-specific settings ────────────────────────
    if platform == "render":
        # Render free tier: 512MB RAM, 750h/month
        os.environ.setdefault("MAX_WORKERS", "50")
        os.environ.setdefault("DRY_RUN", "true")
        os.environ.setdefault("CYCLE_INTERVAL", "60")
        os.environ.setdefault("SITE_URL", "https://jobhunt-pro.onrender.com")

    elif platform == "railway":
        # Railway free tier: $5 credit, 512MB RAM
        os.environ.setdefault("MAX_WORKERS", "50")
        os.environ.setdefault("DRY_RUN", "true")
        os.environ.setdefault("CYCLE_INTERVAL", "60")

    elif platform == "pa":
        # PythonAnywhere free tier
        os.environ.setdefault("MAX_WORKERS", "30")
        os.environ.setdefault("CYCLE_INTERVAL", "120")
        os.environ.setdefault("SITE_URL", "https://jhfguf.pythonanywhere.com")

    else:
        # Local development
        os.environ.setdefault("MAX_WORKERS", "100")
        os.environ.setdefault("CYCLE_INTERVAL", "60")

    # ── Common defaults ───────────────────────────────────
    if not os.getenv("CV_PATH"):
        os.environ["CV_PATH"] = str(ROOT_DIR / "assets" / "Sam_Salameh_CV.pdf")

    logger.info(
        "Config: DRY_RUN=%s MAX_WORKERS=%s CYCLE_INTERVAL=%smin",
        os.getenv("DRY_RUN"),
        os.getenv("MAX_WORKERS"),
        os.getenv("CYCLE_INTERVAL"),
    )


# ═══════════════════════════════════════════════════════════════
# BACKUP DAEMON (asyncio task)
# ═══════════════════════════════════════════════════════════════

async def backup_daemon(interval_hours: int = 6):
    """Run database backups on a timer using core/auto_backup.py.

    Runs alongside the web server in the same event loop.
    Gracefully stops when _shutdown is set.
    """
    global _shutdown
    logger.info(
        "[DB] Backup daemon: every %dh, keeping last 5",
        interval_hours,
    )

    # Wait for web server to be ready
    await asyncio.sleep(20)

    # Run first backup immediately on startup
    logger.info("Running initial backup on startup...")
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_backup_sync)
    except Exception as e:
        logger.error("Initial backup failed: %s", e)

    # Then schedule every N hours
    cycle = 0
    while not _shutdown:
        cycle += 1
        # Sleep in 1s increments to respond to shutdown quickly
        for _ in range(interval_hours * 3600):
            if _shutdown:
                break
            await asyncio.sleep(1)

        if _shutdown:
            break

        logger.info("Scheduled backup #%d starting...", cycle)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _run_backup_sync)
        except Exception as e:
            logger.error("Scheduled backup #%d failed: %s", cycle, e)

    logger.info("Backup daemon stopped")


def _run_backup_sync():
    """Synchronous wrapper for auto_backup.run_backup().

    Runs in executor to avoid blocking the event loop.
    """
    from core.auto_backup import run_backup

    result = run_backup()
    if result["success"]:
        logger.info(
            "OK: Backup OK: %s (%.1f MB, %.1fs) telegram=%s",
            Path(result.get("backup_path", "")).name if result.get("backup_path") else "?",
            result.get("db_size_mb", 0),
            result.get("duration_s", 0),
            result.get("telegram_sent", False),
        )
    else:
        logger.warning("FAIL: Backup FAILED: %s", result.get("error", "unknown"))
    return result


# ═══════════════════════════════════════════════════════════════
# SIGNAL HANDLING
# ═══════════════════════════════════════════════════════════════

def handle_signal(signum, frame):
    """Graceful shutdown handler for SIGTERM/SIGINT."""
    global _shutdown
    if not _shutdown:
        signame = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.info("Received %s — initiating graceful shutdown...", signame)
        _shutdown = True


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Start the web server + backup daemon. Works on all platforms."""
    global _shutdown

    # Parse CLI
    parser = argparse.ArgumentParser(
        description="JobHunt Pro — Cloud Entrypoint"
    )
    parser.add_argument(
        "--render", action="store_true", help="Force Render.com mode"
    )
    parser.add_argument(
        "--railway", action="store_true", help="Force Railway.app mode"
    )
    parser.add_argument(
        "--pa", action="store_true", help="Force PythonAnywhere mode"
    )
    parser.add_argument(
        "--local", action="store_true", help="Force local/dev mode"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Disable backup daemon"
    )
    parser.add_argument(
        "--backup-interval", type=int, default=6,
        help="Backup interval in hours (default: 6)",
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Override PORT env var"
    )
    parser.add_argument(
        "--host", type=str, default=None, help="Override HOST env var"
    )
    args = parser.parse_args()

    # Detect platform
    if args.render:
        platform = "render"
    elif args.railway:
        platform = "railway"
    elif args.pa:
        platform = "pa"
    elif args.local:
        platform = "local"
    else:
        platform = detect_platform()

    # Configure
    configure_platform(platform)

    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.host:
        os.environ["HOST"] = args.host

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    # ── Banner ────────────────────────────────────────────
    logger.info("=" * 55)
    logger.info("   JOBHUNT PRO v%s — Cloud Edition", os.getenv("VERSION", "16.318"))
    logger.info("  Platform: %s", platform.upper())
    logger.info("  URL:      %s", os.getenv("SITE_URL", f"http://{host}:{port}"))
    logger.info("  Health:   http://%s:%s/health", host, port)
    logger.info("  Backup:   %s", "DISABLED" if args.no_backup else f"every {args.backup_interval}h")
    logger.info("=" * 55)

    # ── Register signal handlers ───────────────────────────
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    # SIGBREAK is Windows-specific
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_signal)

    # ── Import app ────────────────────────────────────────
    try:
        from web.app_v2 import app
        logger.info("FastAPI app imported successfully")
    except Exception as e:
        logger.exception("Failed to import web.app_v2: %s", e)
        sys.exit(1)

    # ── Start server + daemon ─────────────────────────────
    import uvicorn

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,  # disable access logs on free tier to save disk
        timeout_keep_alive=5,
        limit_concurrency=50,
        limit_max_requests=5000,  # recycle workers periodically (free tier RAM)
    )
    server = uvicorn.Server(config)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Schedule backup daemon if enabled
        if not args.no_backup:
            loop.create_task(backup_daemon(interval_hours=args.backup_interval))

        # Run uvicorn server (blocks until shutdown)
        loop.run_until_complete(server.serve())

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
    finally:
        _shutdown = True
        logger.info("Shutdown complete. Goodbye! ")


if __name__ == "__main__":
    main()

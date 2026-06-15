"""
JobHunt Pro - Cloud Startup Script
===================================
Handles Railway/Render environment variables and graceful startup.
Runs the FastAPI web server AND background job cycles in a single process.
Works with SQLite on free tier (no PostgreSQL dependency).

Architecture:
  - One process, one event loop
  - Web server (uvicorn) serves the FastAPI dashboard
  - Background asyncio task runs Orchestrator.run_full_cycle() on a timer
  - External cron services can also trigger cycles via /cron/run-cycle endpoint
"""
import os
import sys
import asyncio
import logging
import signal
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure required directories exist
for _dir in ["data", "logs", "sent_mails", "cache"]:
    (ROOT_DIR / _dir).mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(ROOT_DIR / "logs" / "cloud.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Global shutdown flag for graceful termination
_shutdown = False


def configure_cloud_env():
    """Set up environment variables for cloud deployment."""
    # Railway/Render set PORT automatically
    port = os.getenv("PORT", "8000")
    logger.info("Cloud PORT: %s", port)

    # SQLite paths - use /app/data for persistent volume
    data_dir = ROOT_DIR / "data"
    db_name = "jobhunt_saas_v2.db"
    db_path = data_dir / db_name

    # Override DATABASE_URL if not set or if it points to PostgreSQL
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url or database_url.startswith("postgresql"):
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{db_path}"
        logger.info("Using SQLite: %s", db_path)
    else:
        logger.info("Using configured DATABASE_URL")

    # DB_PATH for legacy code
    if not os.getenv("DB_PATH"):
        os.environ["DB_PATH"] = str(data_dir / "sam_max.db")

    # Cloud mode flag
    os.environ["CLOUD_MODE"] = "true"

    # Reduce workers on free tier (limited RAM)
    if not os.getenv("MAX_WORKERS"):
        os.environ["MAX_WORKERS"] = "50"

    # Default to dry run on cloud for safety
    if not os.getenv("DRY_RUN"):
        os.environ["DRY_RUN"] = "true"

    # CV path
    if not os.getenv("CV_PATH"):
        os.environ["CV_PATH"] = "assets/Sam_Salameh_CV.pdf"

    # Background cycle interval (minutes)
    if not os.getenv("CYCLE_INTERVAL"):
        os.environ["CYCLE_INTERVAL"] = "60"

    logger.info("Cloud environment configured:")
    logger.info("  DRY_RUN=%s", os.getenv("DRY_RUN"))
    logger.info("  MAX_WORKERS=%s", os.getenv("MAX_WORKERS"))
    logger.info("  CYCLE_INTERVAL=%s min", os.getenv("CYCLE_INTERVAL"))


def init_sqlite_db():
    """Initialize SQLite database with schema if it doesn't exist."""
    data_dir = ROOT_DIR / "data"
    db_path = data_dir / "jobhunt_saas_v2.db"

    if db_path.exists():
        logger.info("Database already exists: %s", db_path)
        return

    logger.info("Initializing SQLite database: %s", db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create core tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            phone TEXT,
            company_name TEXT,
            user_type TEXT DEFAULT 'jobseeker',
            wallet_balance REAL DEFAULT 0,
            total_spent REAL DEFAULT 0,
            api_key TEXT UNIQUE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cv_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            profile_name TEXT,
            cv_text TEXT,
            cover_letter_template TEXT,
            email_template TEXT,
            skills TEXT,
            experience_years INTEGER,
            target_titles TEXT,
            target_locations TEXT,
            home_country TEXT DEFAULT 'Lebanon',
            min_local_salary REAL DEFAULT 0,
            min_international_salary REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            campaign_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            target_titles TEXT,
            target_locations TEXT,
            target_companies TEXT,
            daily_limit INTEGER DEFAULT 50,
            total_sent INTEGER DEFAULT 0,
            total_replies INTEGER DEFAULT 0,
            total_interviews INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            order_id TEXT UNIQUE NOT NULL,
            service_type TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            crypto_address TEXT,
            tx_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            reference_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            campaign_id TEXT,
            company TEXT,
            job_title TEXT,
            job_url TEXT,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_at TIMESTAMP,
            response_type TEXT
        );
    """)

    conn.commit()
    conn.close()
    logger.info("SQLite database initialized successfully")


async def background_job_cycle():
    """Run Orchestrator.run_full_cycle() on a timer in the background.

    This runs as an asyncio task alongside the web server.
    The cycle interval is configurable via CYCLE_INTERVAL env var (default: 60 min).
    Respects DRY_RUN setting — if true, runs through motions without sending emails.
    """
    global _shutdown
    cycle_interval = int(os.getenv("CYCLE_INTERVAL", "60"))
    is_dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    logger.info("Background job cycle starting (interval=%d min, dry_run=%s)",
                cycle_interval, is_dry_run)

    # Wait briefly for web server to be ready
    await asyncio.sleep(15)

    cycle_count = 0
    while not _shutdown:
        cycle_count += 1
        logger.info("=" * 60)
        logger.info("  BACKGROUND CYCLE #%d - Starting at %s",
                    cycle_count, datetime.now(timezone.utc).isoformat())
        logger.info("=" * 60)

        try:
            from orchestrator import Orchestrator
            orch = Orchestrator()
            result = await orch.run_full_cycle()
            logger.info(
                "Cycle #%d complete: found=%d, applied=%d, followups=%d",
                cycle_count,
                result.get('found', 0),
                result.get('applied', 0),
                result.get('followups', 0)
            )
        except Exception as e:
            logger.exception("Background cycle #%d failed: %s", cycle_count, e)

        if _shutdown:
            break

        # Sleep until next cycle (check shutdown flag every second)
        logger.info("Sleeping %d minutes until next background cycle...", cycle_interval)
        for _ in range(cycle_interval * 60):
            if _shutdown:
                break
            await asyncio.sleep(1)

    logger.info("Background job cycle stopped")


async def run_telegram_bot():
    """Run Telegram bot with 24/7 crash protection and auto-restart.

    Uses BotWatchdog from telegram_enhanced to:
    - Auto-restart on any crash
    - Notify admin on failure
    - Exponential backoff for restarts
    """
    global _shutdown
    await asyncio.sleep(10)
    try:
        from core.telegram_enhanced import start_telegram_bot_enhanced
        logger.info("[BOT] Starting enhanced bot with 24/7 crash protection...")
        await start_telegram_bot_enhanced()
    except Exception as e:
        logger.warning("[BOT] Telegram bot disabled: %s", e)
        while not _shutdown:
            await asyncio.sleep(3600)


def handle_sigterm(signum, frame):
    """Handle SIGTERM for graceful shutdown (sent by Render/Railway on restart)."""
    global _shutdown
    if not _shutdown:
        logger.info("Received signal %s - shutting down gracefully...", signum)
        _shutdown = True


def main():
    """Main entry point for cloud deployment.

    Starts both the web server and background job cycle on the same event loop.
    """
    logger.info("=" * 50)
    logger.info("  JOBHUNT PRO - Cloud Edition")
    logger.info("  Render.com / Railway Free Tier")
    logger.info("=" * 50)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    # Configure environment
    configure_cloud_env()

    # Initialize database
    init_sqlite_db()

    # Import the web app
    from web.app_v2 import app
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    # Create uvicorn server config
    config_data = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        timeout_keep_alive=5,
        limit_concurrency=100,
    )
    server = uvicorn.Server(config_data)

    logger.info("Starting web server on %s:%d", host, port)
    logger.info("Health check: http://%s:%d/health", host, port)
    logger.info("Background job cycle: every %s minutes", os.getenv("CYCLE_INTERVAL", "60"))
    logger.info("Telegram bot polling: enabled")

    try:
        # Run both the web server and background tasks on the same event loop
        # server.serve() is an async method that runs until the server stops
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Schedule background tasks
        bg_task = loop.create_task(background_job_cycle())
        tg_task = loop.create_task(run_telegram_bot())

        # Run the server (blocks until shutdown signal)
        loop.run_until_complete(server.serve())

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.exception("Startup error: %s", e)
    finally:
        global _shutdown
        _shutdown = True
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()

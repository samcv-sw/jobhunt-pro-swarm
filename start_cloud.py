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

# Hijack sqlite3 globally with core.pg_sqlite_shim to transparently use Neon PG
try:
    import core.pg_sqlite_shim as pg_sqlite_shim
    sys.modules['sqlite3'] = pg_sqlite_shim
    print("[HYDRA] Successfully hijacked sqlite3 globally with pg_sqlite_shim")
except Exception as shim_err:
    print(f"[HYDRA] Failed to hijack sqlite3: {shim_err}")

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

    # Database Configuration (Hydra Architecture)
    # Use remote serverless databases (Neon/Turso) if provided, otherwise fallback to local SQLite
    database_url = os.getenv("DATABASE_URL", "")
    
    if database_url and (database_url.startswith("postgresql") or database_url.startswith("libsql")):
        logger.info("HYDRA MODE: Using Distributed Edge Database: %s", database_url.split('@')[-1] if '@' in database_url else database_url)
    else:
        # Fallback to local SQLite only if no remote DB is provided
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{db_path}"
        logger.info("Using Local SQLite (Not Recommended for 1M+ Scale): %s", db_path)

    # DB_PATH for legacy code
    if not os.getenv("DB_PATH"):
        os.environ["DB_PATH"] = str(data_dir / "sam_max.db")

    # Cloud mode flag
    os.environ["CLOUD_MODE"] = "true"

    # [PROJECT APEX] MAXIMIZE ORACLE ARM 24GB RAM
    if not os.getenv("MAX_WORKERS"):
        os.environ["MAX_WORKERS"] = "5000" # Unlocked from 50 to 5000 for 24GB RAM

    # Disable dry run by default for production APEX mode
    if not os.getenv("DRY_RUN"):
        os.environ["DRY_RUN"] = "false"

    # CV path
    if not os.getenv("CV_PATH"):
        os.environ["CV_PATH"] = "assets/Sam_Salameh_CV.pdf"

    # Background cycle interval (minutes) - APEX mode runs constantly
    if not os.getenv("CYCLE_INTERVAL"):
        os.environ["CYCLE_INTERVAL"] = "15"

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

_sender_running = False

async def run_queue_worker_loop():
    """Continuously poll and process tasks from the database job_queue.
    Enables zero-traffic execution of campaigns and background automation tasks.
    """
    global _shutdown
    logger.info("[QUEUE-WORKER] Starting background queue worker loop...")
    
    # Wait 20 seconds for web server to boot up
    await asyncio.sleep(20)
    
    while not _shutdown:
        try:
            from core.job_queue import dequeue_task, complete_task, fail_task
            task = dequeue_task()
            if not task:
                await asyncio.sleep(5)
                continue
                
            task_id = task["id"]
            task_type = task["task_type"]
            payload = task["payload"]
            
            logger.info("[QUEUE-WORKER] Processing task %d: %s", task_id, task_type)
            
            if task_type == "run_campaign":
                campaign_id = payload.get("campaign_id")
                if campaign_id:
                    from core.campaign_runner import run_campaign
                    import config
                    
                    def _run():
                        # We use local sqlite connect which is shimmed globally to Postgres
                        import sqlite3
                        def local_get_db():
                            import os
                            c = sqlite3.connect(os.environ.get('DB_PATH', 'jobhunt_saas_v2.db'), timeout=30)
                            c.row_factory = sqlite3.Row
                            return c
                        asyncio.run(run_campaign(campaign_id, local_get_db, config))
                        
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, _run)
                    complete_task(task_id)
                    logger.info("[QUEUE-WORKER] Task %d completed successfully", task_id)
                else:
                    fail_task(task_id, "Missing campaign_id")
            else:
                # Mock completion for other growth-autopilot tasks
                complete_task(task_id)
                logger.info("[QUEUE-WORKER] Growth task %d of type %s completed (mocked)", task_id, task_type)
                
        except Exception as e:
            logger.error("[QUEUE-WORKER] Error in queue worker loop: %s", e)
            await asyncio.sleep(5)
            
        await asyncio.sleep(1)
        
    logger.info("[QUEUE-WORKER] Background queue worker loop stopped")


async def run_cloud_email_sender_loop():
    """Run scripts/cloud_email_sender.py main() in a background loop.
    Drains the Cloudflare outbox by sending emails via SMTP.
    Runs 24/7 on Render/Fly.io for free, replacing GHA cron.
    """
    global _shutdown, _sender_running
    logger.info("[SENDER] Starting background cloud email sender loop...")
    
    # Wait 30 seconds for web server to boot up
    await asyncio.sleep(30)
    
    while not _shutdown:
        if not _sender_running:
            logger.info("[SENDER] Checking Cloudflare outbox for queued emails...")
            try:
                _sender_running = True
                from scripts.cloud_email_sender import main as run_sender
                # Run the synchronous email claim & send cycle in a separate thread
                # to prevent blocking the async event loop.
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_sender)
            except Exception as e:
                logger.error("[SENDER] Cloud email sender execution failed: %s", e)
            finally:
                _sender_running = False
        else:
            logger.info("[SENDER] Previous sender run is still active. Skipping this cycle.")
            
        if _shutdown:
            break
            
        # Check every 5 minutes (300 seconds)
        logger.info("[SENDER] Sleeping 5 minutes before next outbox check...")
        for _ in range(300):
            if _shutdown:
                break
            await asyncio.sleep(1)
            
    logger.info("[SENDER] Background cloud email sender loop stopped")


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

    import argparse
    parser = argparse.ArgumentParser(description="JobHunt Pro Hydra Startup")
    parser.add_argument("--api-only", action="store_true", help="Run only the FastAPI web server (For Hugging Face/Koyeb)")
    parser.add_argument("--worker-only", action="store_true", help="Run only the background swarm workers (For Oracle Cloud)")
    args, unknown = parser.parse_known_args()

    # Configure environment
    configure_cloud_env()

    # Initialize database (only for local SQLite fallback)
    if not os.getenv("DATABASE_URL", "").startswith(("postgresql", "libsql")):
        init_sqlite_db()

    # Create loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    tasks_to_run = []

    if not args.worker_only:
        # Start Web Server (API)
        from web.app_v2 import app
        import uvicorn
        
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        
        config_data = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=False,
            timeout_keep_alive=15,
            limit_concurrency=2000,
        )
        server = uvicorn.Server(config_data)
        logger.info("Starting web server on %s:%d (Hydra API Head)", host, port)
        tasks_to_run.append(server.serve())

    if not args.api_only:
        # Start Background Workers (Swarm)
        logger.info("Starting Background Swarm Workers (Hydra Compute Head)")
        tasks_to_run.append(background_job_cycle())
        tasks_to_run.append(run_telegram_bot())
        tasks_to_run.append(run_cloud_email_sender_loop())
        tasks_to_run.append(run_queue_worker_loop())

    try:
        if tasks_to_run:
            loop.run_until_complete(asyncio.gather(*tasks_to_run))
        else:
            logger.info("No components selected to run. Use either --api-only or --worker-only, or neither to run both.")

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

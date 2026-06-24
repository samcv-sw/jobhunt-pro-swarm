"""
JobHunt Pro - Single Cycle Run Entrypoint (run_once.py)
Coordinates search, scoring, applying, and follow-ups in a single run.
Designed for daily execution via GitHub Actions (job-hunt.yml).
"""
import sys
import os
import asyncio
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/run_once.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("run_once")

async def main():
    logger.info("=" * 60)
    logger.info(f"JOBHUNT PRO v{config.VERSION} - RUN ONCE CLOUD START")
    logger.info("=" * 60)
    
    # Create logs directory if not exists
    os.makedirs("logs", exist_ok=True)
    
    from orchestrator import Orchestrator
    orch = Orchestrator()
    
    logger.info("[1] Initializing Database & Verification...")
    await orch.db.create_tables()
    
    logger.info("[2] Executing Full Cycle (Search + Scrape + Queue)...")
    cycle_result = await orch.run_full_cycle()
    logger.info(f"    Cycle result: {cycle_result}")
    
    logger.info("[3] Processing Direct Applies (Sending Emails)...")
    # Run direct email applications for any queued jobs in the database
    apply_result = await orch.run_apply(limit=100)
    logger.info(f"    Apply result: {apply_result}")
    
    logger.info("[4] Retrying any failed applications...")
    retry_result = await orch.retry_failed(limit=20)
    logger.info(f"    Retry result: {retry_result}")
    
    logger.info("[5] Fetching final database status...")
    stats = await orch.db.get_stats()
    logger.info(f"    Final Stats: {stats}")
    
    logger.info("=" * 60)
    logger.info("JOBHUNT PRO SINGLE CYCLE RUN COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Run once interrupted by user")
    except Exception as e:
        logger.exception("Fatal error in run_once: %s", e)
        sys.exit(1)
    sys.exit(0)

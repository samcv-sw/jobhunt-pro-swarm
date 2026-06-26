import time
import os
import sys
import logging
import asyncio

# Set up logging
log_dir = "/home/JHFGUF/jobhunt/logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - ALWAYS-ON - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/JHFGUF/jobhunt/logs/always_on.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting Always-on Campaign Loop...")

# Add project root to path
sys.path.insert(0, "/home/JHFGUF/jobhunt")

async def run_loop():
    while True:
        logger.info("Triggering campaign run cycle...")
        try:
            from core.multi_tenant import MultiTenantRunner
            runner = MultiTenantRunner(company_limit=15, max_campaigns=3)
            result = await runner.tick()
            logger.info(f"Cycle complete: processed {result.get('campaigns_processed', 0)} campaigns, sent {result.get('emails_sent', 0)} applications")
        except Exception as e:
            logger.error(f"Error during campaign cycle: {e}", exc_info=True)
        
        logger.info("Sleeping for 15 minutes...")
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(run_loop())

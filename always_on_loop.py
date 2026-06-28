import time
import os
import sys
import logging
import asyncio
import io

# ── Fix Windows console encoding for emoji-safe logging ──
if sys.stdout.encoding is None or sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding is None or sys.stderr.encoding.upper() not in ("UTF-8", "UTF8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Resolve paths dynamically to support both local and PythonAnywhere environments
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - ALWAYS-ON - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "always_on.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting Always-on Campaign Loop — MAXIMUM THROUGHPUT MODE")

# Add project root to path
sys.path.insert(0, base_dir)

async def run_loop():
    consecutive_empty = 0
    while True:
        logger.info("Triggering campaign run cycle...")
        sleep_time = 1  # Default: 1 second between cycles for max throughput
        try:
            from core.multi_tenant import MultiTenantRunner
            runner = MultiTenantRunner(company_limit=15, max_campaigns=10)
            result = await runner.tick()
            processed = result.get('campaigns_processed', 0)
            sent = result.get('emails_sent', 0)
            logger.info(f"Cycle complete: processed {processed} campaigns, sent {sent} applications")
            
            if processed > 0:
                # If campaigns were processed, tick every 1 second (no delay)
                sleep_time = 1
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                # If no campaigns for 10+ cycles, still only wait 3s max
                if consecutive_empty > 10:
                    sleep_time = 3
                else:
                    sleep_time = 1
        except Exception as e:
            logger.error(f"Error during campaign cycle: {e}", exc_info=True)
            sleep_time = 5  # Short delay on error, then retry fast
        
        logger.info(f"Sleeping for {sleep_time} seconds...")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(run_loop())

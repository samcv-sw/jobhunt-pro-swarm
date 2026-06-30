"""
Cloud Campaign Loop — Designed for PythonAnywhere Scheduled Tasks
Runs MultiTenantRunner.tick() once per invocation.
Triggered every 5 minutes by PA cron, or via /api/cron/tick endpoint.

Usage:
    python cloud_loop.py [--company-limit 15] [--max-campaigns 3]

Environment Variables Required (set in PA):
    FORCE_PG=1
    DATABASE_URL=postgresql://...
    NEON_DATABASE_URL=postgresql://...
    GROQ_API_KEY=...
    (all other .env vars)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Resolve paths dynamically
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

# Configure logging
log_dir = os.path.join(base_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - CLOUD-LOOP - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "cloud_loop.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_tick(company_limit=15, max_campaigns=3):
    """Run a single tick of the campaign loop. Returns result dict."""
    import asyncio
    
    logger.info(f"Cloud tick starting — company_limit={company_limit}, max_campaigns={max_campaigns}")
    
    async def _tick():
        from core.multi_tenant import MultiTenantRunner
        runner = MultiTenantRunner(company_limit=company_limit, max_campaigns=max_campaigns)
        result = await runner.tick()
        return result
    
    try:
        result = asyncio.run(_tick())
        campaigns = result.get('campaigns_processed', 0)
        sent = result.get('emails_sent', 0)
        logger.info(f"Cloud tick complete: {campaigns} campaigns, {sent} emails sent")
        return {"status": "ok", "campaigns": campaigns, "sent": sent}
    except Exception as e:
        logger.error(f"Cloud tick failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud Campaign Loop — single tick")
    parser.add_argument("--company-limit", type=int, default=15, help="Max companies per campaign")
    parser.add_argument("--max-campaigns", type=int, default=3, help="Max campaigns to process")
    args = parser.parse_args()
    
    result = run_tick(args.company_limit, args.max_campaigns)
    print(json.dumps(result))

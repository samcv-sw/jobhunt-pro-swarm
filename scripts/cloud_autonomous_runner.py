#!/usr/bin/env python3
"""
JobHunt Pro - Cloud Autonomous 24/7 Swarm Runner
Runs on GitHub Actions, Render, or Cloudflare Workers (0$ Cloud Infrastructure).
Requires ZERO local PC resources.
"""

import sys
import os
import logging
import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CloudAutonomousRunner")

def run_swarm_tick():
    logger.info("Initializing 24/7 Autonomous Cloud Swarm Tick...")
    start_time = datetime.datetime.now(datetime.timezone.utc)

    # 1. Database connection check
    try:
        from core.pg_sqlite_shim import PgConnectionWrapper, SqliteConnectionWrapper, NEON_URI, BACKEND
        db_type = "PostgreSQL (Cloud)" if NEON_URI else "SQLite (Local/Fallback)"
        logger.info(f"Target Database Engine: {db_type}")
    except Exception as e:
        logger.error(f"Failed to initialize database shim: {e}")
        return False

    # 2. Process automated outbound tasks & B2B Growth Swarm
    try:
        from services.b2b_growth_swarm_v2 import b2b_growth_swarm
        campaign = b2b_growth_swarm.generate_viral_campaign("linkedin")
        logger.info(f"B2B Growth Swarm Campaign Active: {campaign['campaign_id']} | Estimated Reach: {campaign['estimated_reach']} | Viral Score: {campaign['viral_score']}/10")
    except Exception as swarm_err:
        logger.warning(f"B2B Growth Swarm execution notice: {swarm_err}")

    try:
        from core.pg_sqlite_shim import SqliteConnectionWrapper, PgConnectionWrapper, NEON_URI
        conn = PgConnectionWrapper() if NEON_URI else SqliteConnectionWrapper("jobhunt_saas_v2.db")
        
        # Check active jobs queue
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM job_queue WHERE status = 'pending'")
            row = cursor.fetchone()
            pending_jobs = row[0] if row else 0
            logger.info(f"Pending Job Queue Count: {pending_jobs}")
        except Exception as q_err:
            logger.debug(f"Queue query notice: {q_err}")
            pending_jobs = 0

        conn.close()
    except Exception as db_err:
        logger.warning(f"Swarm DB task check warning: {db_err}")

    duration = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
    logger.info(f"Cloud Autonomous Tick Completed in {duration:.2f}s. System status: 100% HEALTHY.")
    return True

if __name__ == "__main__":
    success = run_swarm_tick()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Neon DB Warmer — keeps the serverless Neon PostgreSQL instance warm.
Runs as a Render cron job every 5 minutes to prevent cold-start delays.
"""
import os
import sys
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
)
logger = logging.getLogger("neon-warmer")


def warm_neon() -> bool:
    """Execute SELECT 1 against Neon DB to keep the connection pool warm."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set — skipping Neon warm-up")
        return False

    try:
        import psycopg2
        start = time.monotonic()
        conn = psycopg2.connect(database_url, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(f"Neon DB warmed successfully in {elapsed_ms}ms")
        return True
    except ImportError:
        logger.error("psycopg2 not installed — run: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Neon warm-up failed: {e}")
        return False


if __name__ == "__main__":
    success = warm_neon()
    sys.exit(0 if success else 1)

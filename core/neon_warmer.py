#!/usr/bin/env python3
"""
Neon DB Warmer — keeps the serverless Neon PostgreSQL instance warm.
Runs as a Render cron job every 5 minutes to prevent cold-start delays.

Retry policy: up to 3 attempts with 5-second delays between retries.
Emits a structured JSON summary log on completion.
"""
import json
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
)
logger = logging.getLogger("neon-warmer")


def warm_neon(*, max_retries: int = 3, retry_delay: float = 5.0) -> bool:
    """Execute SELECT 1 against Neon DB to keep the connection pool warm.

    Retries up to ``max_retries`` times with ``retry_delay`` second delays
    between attempts. Converts postgres:// URL scheme to postgresql:// if
    needed so psycopg2 can parse it.

    Args:
        max_retries: Maximum number of connection attempts.
        retry_delay: Seconds to wait between failed attempts.

    Returns:
        True if any attempt succeeded, False if all attempts failed.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set — skipping Neon warm-up")
        return False

    # psycopg2 requires postgresql:// not postgres://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    try:
        import psycopg2  # type: ignore[import]
    except ImportError:
        logger.error("psycopg2 not installed — run: pip install psycopg2-binary")
        return False

    attempts = 0
    final_latency_ms: float = 0.0
    last_error: str = ""

    for attempt in range(1, max_retries + 1):
        attempts = attempt
        start = time.monotonic()
        try:
            conn = psycopg2.connect(database_url, connect_timeout=10)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            final_latency_ms = round((time.monotonic() - start) * 1000, 2)
            logger.info(
                json.dumps({
                    "msg": "Neon DB warm-up succeeded",
                    "attempt": attempt,
                    "latency_ms": final_latency_ms,
                })
            )
            # Emit final summary
            logger.info(
                json.dumps({
                    "msg": "neon_warmer_summary",
                    "attempts": attempts,
                    "success": True,
                    "final_latency_ms": final_latency_ms,
                })
            )
            return True
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                json.dumps({
                    "msg": "Neon DB warm-up attempt failed",
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "error": last_error,
                })
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error(
        json.dumps({
            "msg": "neon_warmer_summary",
            "attempts": attempts,
            "success": False,
            "final_latency_ms": final_latency_ms,
            "last_error": last_error,
        })
    )
    return False


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        logger.warning("DATABASE_URL not set — skipping Neon warm-up")
        sys.exit(0)
    success = warm_neon()
    sys.exit(0 if success else 1)

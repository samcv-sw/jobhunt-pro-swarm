"""
Neon Warmer (Phase 2 completion)
Pings the database every 4 minutes to prevent it from spinning down.
"""
import time
import logging
from core.pg_sqlite_shim import connect
import config

logger = logging.getLogger(__name__)

def warm_database():
    while True:
        try:
            conn = connect("dummy.db")
            conn.execute("SELECT 1")
            conn.close()
            logger.info("[NeonWarmer] Successfully pinged database.")
        except Exception as e:
            logger.error(f"[NeonWarmer] Ping failed: {e}")
        
        # Sleep for 4 minutes
        time.sleep(240)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Neon Warmer...")
    warm_database()

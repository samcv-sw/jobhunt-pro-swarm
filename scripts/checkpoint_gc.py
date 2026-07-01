import os
import asyncio
import logging
from psycopg import AsyncConnection

# The Hydra 2026: Garbage Collection for LangGraph Checkpoints
# Run this script via a cron job (e.g. daily at 3 AM) to prevent the Oracle Free Tier
# from running out of its 200GB storage limit.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CheckpointGC")

DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
# Delete checkpoints older than 3 days
DAYS_TO_KEEP = 3

async def run_gc():
    logger.info(f"Starting Checkpoint Garbage Collection. Keeping last {DAYS_TO_KEEP} days.")
    try:
        async with await AsyncConnection.connect(DB_URI) as conn:
            # LangGraph stores states in 'checkpoints' and 'checkpoint_writes' tables (depending on version)
            async with conn.cursor() as cur:
                # Assuming standard langgraph table schema with a timestamp column
                # Delete from checkpoint_writes if exists
                try:
                    await cur.execute(f"DELETE FROM checkpoint_writes WHERE timestamp < NOW() - INTERVAL '{DAYS_TO_KEEP} days';")
                    logger.info("Cleared old checkpoint_writes.")
                except Exception:
                    await conn.rollback()
                    logger.warning("checkpoint_writes table not found or missing timestamp column.")
                
                # Delete from checkpoints
                try:
                    await cur.execute(f"DELETE FROM checkpoints WHERE timestamp < NOW() - INTERVAL '{DAYS_TO_KEEP} days';")
                    logger.info("Cleared old checkpoints.")
                except Exception:
                    await conn.rollback()
                    logger.warning("checkpoints table not found or missing timestamp column.")
                
                await conn.commit()
                logger.info("Garbage Collection Complete.")
    except Exception as e:
        logger.error(f"Garbage collection failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_gc())

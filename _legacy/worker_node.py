import asyncio
import os
import logging
import json
try:
    import asyncpg
except ImportError:
    print("FATAL: asyncpg is required for cloud worker nodes. Please install it via 'pip install asyncpg'.")
    exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("WorkerNode")

NEON_URI = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")

class CloudWorker:
    """
    PROJECT OMEGA - Cloud Worker Node
    Pulls jobs from Neon Postgres queue using FOR UPDATE SKIP LOCKED.
    Can be deployed horizontally across Hugging Face, Render, and Fly.io for 0$ scale.
    """
    def __init__(self):
        self.pool = None
        if not NEON_URI:
            logger.error("NEON_DATABASE_URL environment variable is missing.")
            exit(1)

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=NEON_URI, min_size=1, max_size=10)
        logger.info("Worker Node connected to Neon Postgres.")

    async def process_jobs(self):
        """Poll the database for 'new' jobs, lock them, and process them."""
        logger.info("Listening for new jobs...")
        
        while True:
            async with self.pool.acquire() as conn:
                # Use Postgres as a queue (Skip Locked)
                row = await conn.fetchrow("""
                    UPDATE jobs
                    SET status = 'processing', updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = (
                        SELECT job_id FROM jobs 
                        WHERE status = 'new' 
                        ORDER BY created_at ASC 
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    RETURNING job_id, title, company, email;
                """)

                if row:
                    job_id, title, company, email = row
                    logger.info(f"Processing Job [{job_id}]: {title} @ {company}")
                    
                    try:
                        # SIMULATE PROCESSING AND AI TAILORING
                        await asyncio.sleep(2) # Simulate work
                        
                        logger.info(f"Successfully processed {job_id}. Marking as applied.")
                        await conn.execute("""
                            UPDATE jobs SET status = 'applied', updated_at = CURRENT_TIMESTAMP 
                            WHERE job_id = $1
                        """, job_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing {job_id}: {e}")
                        await conn.execute("""
                            UPDATE jobs SET status = 'failed', updated_at = CURRENT_TIMESTAMP 
                            WHERE job_id = $1
                        """, job_id)
                else:
                    # Queue is empty, sleep before polling again
                    await asyncio.sleep(5)

    async def start(self):
        await self.connect()
        try:
            await self.process_jobs()
        finally:
            if self.pool:
                await self.pool.close()

if __name__ == "__main__":
    worker = CloudWorker()
    asyncio.run(worker.start())

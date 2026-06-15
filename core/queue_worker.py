import asyncio
import logging
from core.database import db

logger = logging.getLogger(__name__)

class PostgresQueueWorker:
    """
    $0 Enterprise Message Queue using PostgreSQL `FOR UPDATE SKIP LOCKED`.
    Replaces volatile asyncio.create_task() with robust, persistent workers.
    """
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self._running = False

    async def start(self):
        self._running = True
        logger.info("Started PostgreSQL Task Queue Worker")
        while self._running:
            try:
                await self.process_next_batch()
            except Exception as e:
                logger.error(f"Queue Worker Error: {e}")
            await asyncio.sleep(2)  # Poll every 2 seconds

    def stop(self):
        self._running = False

    async def process_next_batch(self):
        if not db.pool:
            return

        async with db.pool.acquire() as conn:
            # 1. Fetch pending jobs and lock them atomically
            # The CTE selects rows, locks them, and updates them to 'processing'
            locked_jobs = await conn.fetch(f"""
                WITH claim AS (
                    SELECT id FROM applications 
                    WHERE status = 'pending' 
                    AND (locked_at IS NULL OR locked_at < NOW() - INTERVAL '10 minutes')
                    ORDER BY created_at ASC 
                    LIMIT {self.max_concurrent} 
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE applications a
                SET status = 'processing', locked_at = NOW()
                FROM claim c
                WHERE a.id = c.id
                RETURNING a.*
            """)

            if not locked_jobs:
                return

            logger.info(f"Worker picked up {len(locked_jobs)} pending jobs")

            # 2. Process concurrently
            tasks = [self.execute_job(conn, dict(job)) for job in locked_jobs]
            await asyncio.gather(*tasks)

    async def execute_job(self, conn, job: dict):
        job_id = job['id']
        try:
            logger.info(f"Processing application {job_id} for user {job['user_id']}")
            
            # --- Insert complex RAG / Email logic here ---
            # Simulate processing delay
            await asyncio.sleep(1) 
            
            # 3. Mark successful
            await conn.execute("""
                UPDATE applications 
                SET status = 'completed', locked_at = NULL, updated_at = NOW()
                WHERE id = $1
            """, job_id)
            logger.info(f"Successfully processed application {job_id}")

        except Exception as e:
            # 4. Mark failed and increment retry
            logger.error(f"Failed to process application {job_id}: {e}")
            await conn.execute("""
                UPDATE applications 
                SET status = CASE WHEN retry_count >= 3 THEN 'failed' ELSE 'pending' END,
                    error_log = $1,
                    retry_count = retry_count + 1,
                    locked_at = NULL,
                    updated_at = NOW()
                WHERE id = $2
            """, str(e), job_id)

queue_worker = PostgresQueueWorker()

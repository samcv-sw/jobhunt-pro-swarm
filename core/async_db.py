import os
import logging
import json
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_URL") or os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_SYNC") or ""
if NEON_URI and NEON_URI.startswith("postgresql://"):
    NEON_URI = NEON_URI.replace("postgresql://", "postgresql+asyncpg://", 1)

class AsyncDatabase:
    """
    APEX MATRIX: Asynchronous Database Connection Manager
    Supports aiosqlite (fallback) and asyncpg (Neon Postgres) for deep concurrency.
    """
    def __init__(self):
        self.backend = "sqlite"
        self.pool = None
        self._lock = asyncio.Lock()

    async def connect(self):
        async with self._lock:
            if self.pool:
                return

            if "postgres" in NEON_URI:
                try:
                    import asyncpg
                    # We strip postgresql+asyncpg:// down to postgresql:// for asyncpg connect
                    connect_uri = NEON_URI.replace("postgresql+asyncpg://", "postgresql://")
                    self.pool = await asyncpg.create_pool(dsn=connect_uri, min_size=1, max_size=20)
                    self.backend = "pg"
                    logger.info("APEX MATRIX: Connected to Neon Postgres via asyncpg pool.")
                except Exception as e:
                    logger.error(f"Failed to connect to Neon asyncpg: {e}. Falling back to aiosqlite.")
                    await self._init_sqlite()
            else:
                await self._init_sqlite()

    async def _init_sqlite(self):
        import aiosqlite
        db_path = os.getenv("SQLITE_PATH", "saas_v2.db")
        self.pool = await aiosqlite.connect(db_path)
        self.pool.row_factory = aiosqlite.Row
        self.backend = "sqlite"
        logger.info(f"APEX MATRIX: Connected to SQLite via aiosqlite at {db_path}.")

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        if not self.pool: await self.connect()
        
        if self.backend == "pg":
            # Convert ? to $1, $2 for asyncpg
            pg_query = self._convert_query_to_pg(query)
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(pg_query, *args)
                return dict(row) if row else None
        else:
            async with self.pool.execute(query, args) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def execute(self, query: str, *args):
        if not self.pool: await self.connect()
        
        if self.backend == "pg":
            pg_query = self._convert_query_to_pg(query)
            async with self.pool.acquire() as conn:
                return await conn.execute(pg_query, *args)
        else:
            await self.pool.execute(query, args)
            await self.pool.commit()

    def _convert_query_to_pg(self, query: str) -> str:
        # Convert SQLite ? parameters to PostgreSQL $1, $2, etc.
        parts = query.split('?')
        if len(parts) == 1:
            return query
        result = parts[0]
        for i, part in enumerate(parts[1:], 1):
            result += f"${i}" + part
        return result

async_db = AsyncDatabase()

async def async_dequeue_task() -> Optional[Dict[str, Any]]:
    """
    APEX MATRIX: Atomically dequeues a task using SKIP LOCKED in asyncpg.
    """
    if not async_db.pool: await async_db.connect()

    try:
        if async_db.backend == "pg":
            query = """
                UPDATE job_queue 
                SET status = 'running', locked_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id FROM job_queue 
                    WHERE (status = 'pending' OR status = 'failed')
                      AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP)
                    ORDER BY priority ASC, next_retry_at ASC, created_at ASC 
                    LIMIT 1 
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, task_type, payload
            """
            async with async_db.pool.acquire() as conn:
                row = await conn.fetchrow(query)
                if row:
                    return {"id": row["id"], "task_type": row["task_type"], "payload": json.loads(row["payload"])}
        else:
            # SQLite fallback
            query = """
                SELECT id, task_type, payload FROM job_queue 
                WHERE (status = 'pending' OR status = 'failed')
                  AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP)
                ORDER BY priority ASC, next_retry_at ASC, created_at ASC 
                LIMIT 1
            """
            async with async_db.pool.execute(query) as cursor:
                row = await cursor.fetchone()
                if row:
                    task_id = row["id"]
                    await async_db.pool.execute("UPDATE job_queue SET status = 'running', locked_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
                    await async_db.pool.commit()
                    return {"id": task_id, "task_type": row["task_type"], "payload": json.loads(row["payload"])}
    except Exception as e:
        logger.error(f"Async dequeue failed: {e}")
    return None

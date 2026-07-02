import os
import asyncio
import logging
from procrastinate import App, AsyncpgConnector

logger = logging.getLogger(__name__)

NEON_URL = os.getenv("DATABASE_URL", "")
if NEON_URL.startswith("postgresql+asyncpg://"):
    # Procrastinate AsyncpgConnector expects postgresql://
    NEON_URL = NEON_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

# Strip -pooler suffix to establish a bifurcated, direct connection for LISTEN/NOTIFY pub/sub
NEON_URL = NEON_URL.replace("-pooler.", ".")

# Initialize Procrastinate App
connector = AsyncpgConnector(dsn=NEON_URL)
app = App(connector=connector)

@app.task(queue="default", queueing_lock="ai_resume_{user_id}_{job_id}")
async def generate_ai_resume(user_id: int, job_id: int):
    """
    Background task to generate an AI resume.
    """
    logger.info(f"Starting AI Resume Generation for User {user_id}, Job {job_id}")
    # Simulating long-running AI task
    await asyncio.sleep(5)
    logger.info(f"Finished AI Resume Generation for User {user_id}, Job {job_id}")

async def start_worker():
    """Start Procrastinate worker asynchronously with aggressive garbage collection."""
    async with app.open_async():
        await app.run_worker_async(install_signal_handlers=False, delete_jobs="always")

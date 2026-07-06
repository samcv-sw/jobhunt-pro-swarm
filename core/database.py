import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Fetch Neon URL from .env, ensure it uses asyncpg driver
NEON_URL = os.getenv("DATABASE_URL", "")
if NEON_URL.startswith("postgresql://"):
    NEON_URL = NEON_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Ensure statement_cache_size=0 to avoid PgBouncer transaction mode errors
connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_cache_size": 0,
}

from sqlalchemy.pool import NullPool

# Pool size is handled by PgBouncer; SQLAlchemy should use NullPool to prevent dual-pooling
engine = create_async_engine(
    NEON_URL,
    poolclass=NullPool,
    connect_args=connect_args,
    pool_pre_ping=True,  # Mandatory for Serverless / PgBouncer stability
    echo=False
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db_session():
    """Dependency for FastAPI endpoints with exponential backoff for cold starts."""
    retries = 5
    backoff = 1
    for attempt in range(retries):
        try:
            async with AsyncSessionLocal() as session:
                yield session
                break
        except OperationalError as e:
            if attempt < retries - 1:
                logger.warning(f"Database connection failed. Retrying in {backoff} seconds...")
                import random
                await asyncio.sleep(backoff + random.uniform(0, 0.5))
                backoff *= 2
            else:
                logger.error("Max database retries reached.")
                raise e

# Backward compatibility alias for aiosqlite/asyncpg pool manager
from core.async_db import async_db as db

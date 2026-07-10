import asyncio
import logging
import os
from typing import AsyncGenerator, Any

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
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

class Database:
    """Enterprise Database Manager Wrapper for backward compatibility."""

    def __init__(self) -> None:
        pass

    def _get_conn(self) -> Any:
        """Returns a connection for raw SQL execution."""
        from core.pg_sqlite_shim import connect
        return connect()

    def get_session(self) -> AsyncSession:
        """Returns an async session for SQLAlchemy ORM compatibility."""
        return AsyncSessionLocal()

    async def create_tables(self) -> None:
        """Creates tables using raw schema or SQLAlchemy metadata."""
        from core.pg_sqlite_shim import connect
        with connect() as conn:
            # Create jobs table if it's missing (legacy schema compatibility)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT,
                    title TEXT,
                    location TEXT,
                    url TEXT,
                    score INTEGER,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    response_type TEXT,
                    response_text TEXT
                )
            """)
            conn.commit()

    async def close(self) -> None:
        """No-op for connection pool closing."""
        pass



# Backward compatibility alias for aiosqlite/asyncpg pool manager

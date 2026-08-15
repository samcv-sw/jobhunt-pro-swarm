import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

def format_neon_connection_string(url: str) -> str:
    """Format PostgreSQL/Neon connection string with pooler hostname and required query parameters."""
    if not url or "sqlite" in url:
        return url

    scheme_mapping = {
        "postgresql+asyncpg": "postgresql",
        "postgres": "postgresql",
    }

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme
        base_scheme = scheme_mapping.get(scheme, scheme)
        if base_scheme != "postgresql" and base_scheme != "postgres":
            return url

        hostname = parsed.hostname
        new_host = hostname
        if hostname and "neon.tech" in hostname and "-pooler" not in hostname:
            parts = hostname.split(".", 1)
            new_host = f"{parts[0]}-pooler.{parts[1]}" if len(parts) == 2 else f"{hostname}-pooler"

        netloc_parts = []
        if parsed.username:
            user_pass = parsed.username
            if parsed.password is not None:
                user_pass += f":{parsed.password}"
            netloc_parts.append(f"{user_pass}@")
        netloc_parts.append(new_host or "")
        netloc_parts.append(":5432")
        new_netloc = "".join(netloc_parts)

        query_params = dict(parse_qsl(parsed.query))
        query_params["sslmode"] = "require"
        query_params["prepareThreshold"] = "0"
        new_query = urlencode(query_params)

        return urlunparse((
            scheme,
            new_netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
    except Exception as e:
        logger.error(f"Error formatting Neon connection string: {e}")
        return url

# Fetch PostgreSQL URL from env, supporting POSTGRES_URL, DATABASE_URL, and NEON_URL
_raw_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or os.getenv("NEON_URL") or ""
if _raw_url and "sqlite" not in _raw_url:
    NEON_URL = format_neon_connection_string(_raw_url)
    if NEON_URL.startswith("postgresql://"):
        NEON_URL = NEON_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif NEON_URL.startswith("postgres://"):
        NEON_URL = NEON_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    NEON_URL = ""

# Fallback to local SQLite if no remote PostgreSQL is configured
IS_SQLITE = not NEON_URL or "sqlite" in NEON_URL
if not NEON_URL:
    NEON_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./data/jobhunt_saas_v2.db")

# Ensure statement_cache_size=0 to avoid PgBouncer transaction mode errors
connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_cache_size": 0,
}

if not IS_SQLITE and "sslmode" in NEON_URL:
    if "?" in NEON_URL:
        base_url, query = NEON_URL.split("?", 1)
        params = [p for p in query.split("&") if not p.startswith("sslmode=")]
        NEON_URL = f"{base_url}?{'&'.join(params)}" if params else base_url
    connect_args["ssl"] = True

from sqlalchemy.pool import QueuePool

if IS_SQLITE:
    engine = create_async_engine(
        NEON_URL,
        connect_args={"timeout": 30.0},
        echo=False
    )
else:
    # Configure highly-resilient Connection Pool to survive Neon Cold Starts.
    # Using QueuePool instead of NullPool to eliminate TCP handshake latency on every request.
    # Conserve connections under serverless limits (pool_size=2, max_overflow=2).
    engine = create_async_engine(
        NEON_URL,
        pool_size=2,
        max_overflow=1,
        pool_timeout=30,       # Wait longer during cold starts
        pool_recycle=280,      # Recycle stale connections before 5-minute Neon suspend
        pool_pre_ping=True,    # Test connection viability before handing out
        connect_args=connect_args,
        echo=False
    )

from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import event

# Enable Foreign Keys and WAL mode for SQLite (with PythonAnywhere / NFS guard)
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in type(dbapi_connection).__name__.lower() or isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        is_pa_or_nfs = bool(
            os.environ.get("PYTHONANYWHERE_SITE")
            or os.environ.get("PYTHONANYWHERE_DOMAIN")
            or os.environ.get("NFS_MODE", "").lower() in ("1", "true", "yes")
            or os.environ.get("DISABLE_WAL", "").lower() in ("1", "true", "yes")
        )
        if is_pa_or_nfs:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        else:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB Cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB Memory Mapped I/O
        cursor.execute("PRAGMA busy_timeout=30000")  # 30s lock tolerance
        cursor.close()

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints with exponential backoff for cold starts."""
    retries = 5
    backoff = 1
    session = None
    for attempt in range(retries):
        try:
            session = AsyncSessionLocal()
            # Validate connection viability prior to yielding (survives cold starts)
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            break
        except OperationalError as e:
            if session:
                await session.close()
                session = None
            if attempt < retries - 1:
                logger.warning(f"Database connection failed. Retrying in {backoff} seconds...")
                import random
                await asyncio.sleep(backoff + random.uniform(0, 0.5))
                backoff *= 2
            else:
                logger.error("Max database retries reached.")
                raise e
    try:
        yield session
    finally:
        if session:
            await session.close()

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
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_created ON jobs (company, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs (status)")
            conn.execute("CREATE TABLE IF NOT EXISTS campaign_emails (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, recipient TEXT, subject TEXT, body TEXT, status TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, campaign_id TEXT, responded_at TIMESTAMP)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_emails_dedup_365 ON campaign_emails (recipient, sent_at, user_id)")
            conn.execute("CREATE TABLE IF NOT EXISTS cv_profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, profile_name TEXT, cv_text TEXT, target_titles TEXT, target_locations TEXT, min_local_salary REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cv_profiles_user_id ON cv_profiles (user_id)")
            conn.commit()


    async def close(self) -> None:
        """No-op for connection pool closing."""
        pass

    async def get_unscored_jobs(self, limit: int = 200) -> list[dict]:
        """Return jobs not yet scored (score NULL or status 'new') — IMP-230."""
        def _query() -> list[dict]:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "SELECT * FROM jobs WHERE score IS NULL OR status = 'new' "
                    "ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        return await asyncio.to_thread(_query)

    async def get_scored_jobs(self, min_score: int = 0, limit: int = 200) -> list[dict]:
        """Return jobs whose score meets or exceeds min_score — IMP-230."""
        def _query() -> list[dict]:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "SELECT * FROM jobs WHERE score >= ? ORDER BY score DESC LIMIT ?",
                    (min_score, limit),
                )
                return [dict(row) for row in cur.fetchall()]
        return await asyncio.to_thread(_query)

    async def get_failed_jobs(self, limit: int = 2000) -> list[dict]:
        """Return jobs marked with a failed status — IMP-230."""
        def _query() -> list[dict]:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "SELECT * FROM jobs WHERE status = 'failed' ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        return await asyncio.to_thread(_query)

    async def get_jobs_by_status(self, status: str, limit: int = 2000) -> list[dict]:
        """Return jobs filtered by status — IMP-230."""
        def _query() -> list[dict]:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY id DESC LIMIT ?",
                    (status, limit),
                )
                return [dict(row) for row in cur.fetchall()]
        return await asyncio.to_thread(_query)



# Backward compatibility alias for aiosqlite/asyncpg pool manager
from core.async_db import async_db as db
db.disconnect = db.close

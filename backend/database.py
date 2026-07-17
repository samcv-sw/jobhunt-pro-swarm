import asyncio
import logging
import os

_db_logger = logging.getLogger(__name__)
from sqlite3 import Connection as SQLite3Connection

# ─────────────────────────────────────────────────────────────────────────────
# Database Strategy: Turso-first, local SQLite fallback
#
# Priority order:
#   1. TURSO_DATABASE_URL set  →  use Turso (libsql) edge DB (free 8GB tier)
#   2. LOCAL_DATABASE_URL set  →  use custom local SQLite path
#   3. Neither set             →  use default local SQLite file
#
# Set these in your environment / Koyeb secrets:
#   TURSO_DATABASE_URL=libsql://<db-name>.turso.io
#   TURSO_AUTH_TOKEN=<your-token>
# ─────────────────────────────────────────────────────────────────────────────
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def format_neon_connection_string(url: str) -> str:
    if not url:
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

        return urlunparse(
            (scheme, new_netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )
    except Exception as e:
        _db_logger.error(f"Error formatting Neon connection string: {e}")
        return url


TURSO_URL = os.getenv("TURSO_DATABASE_URL")  # e.g. libsql://my-db.turso.io
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")
LOCAL_DB_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./data/jobhunt_saas_v2.db")
REMOTE_PG_URL = (
    format_neon_connection_string(os.getenv("DATABASE_URL")) if os.getenv("DATABASE_URL") else None
)


def _build_active_url() -> str:
    """Return the resolved async database URL at startup, logging the active backend."""
    if TURSO_URL:
        # libsql+aiosqlite over HTTPS — aiosqlite supports the libsql URL scheme
        # when the libsql-experimental package is installed.
        url = TURSO_URL.replace("libsql://", "sqlite+aiosqlite://")
        _db_logger.info('{"msg": "Connecting to Turso edge database", "url": "%s"}', TURSO_URL)
        return url
    if REMOTE_PG_URL:
        _db_logger.info('{"msg": "Connecting to remote PostgreSQL"}')
        url = REMOTE_PG_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url
    _db_logger.info('{"msg": "Using local SQLite fallback", "url": "%s"}', LOCAL_DB_URL)
    return LOCAL_DB_URL


ACTIVE_DB_URL = _build_active_url()

# ─────────────────────────────────────────────────────────────────────────────
# Connection pool: adapt to the active database driver
# ─────────────────────────────────────────────────────────────────────────────
engine_kwargs: dict = {
    "echo": False,
    "execution_options": {"isolation_level": "AUTOCOMMIT"},
}

if "sqlite" in ACTIVE_DB_URL:
    # SQLite / Turso (via aiosqlite): busy timeout, no pooling
    connect_args: dict = {"timeout": 30.0}
    if TURSO_AUTH_TOKEN:
        connect_args["auth_token"] = TURSO_AUTH_TOKEN
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL: production-hardened pool tuned for Neon free tier
    # - pool_size=3: Neon free allows 10 concurrent conns; leaving headroom
    # - pool_recycle=280: Neon serverless auto-suspends at 300s idle; recycle at 280s to avoid stale conns
    # - pool_pre_ping=True: detects stale/timed-out connections before use (essential for Neon)
    # - max_overflow=2: allows short bursts without connection exhaustion
    engine_kwargs.update(
        {
            "pool_size": 3,  # baseline concurrent connections
            "max_overflow": 2,  # burst headroom (total max = 5, within Neon free-tier limit)
            "pool_recycle": 280,  # recycle stale connections before Neon 300s auto-suspend
            "pool_timeout": 30,  # max wait for a free slot before raising OperationalError
            "pool_pre_ping": True,  # heartbeat SELECT 1 before checkout — detects stale Neon conns
        }
    )
    if "?" in ACTIVE_DB_URL:
        base_url, query = ACTIVE_DB_URL.split("?", 1)
        params = []
        for p in query.split("&"):
            if not (
                p.startswith("sslmode=")
                or p.startswith("prepareThreshold=")
                or p.startswith("prepare_threshold=")
            ):
                params.append(p)
        ACTIVE_DB_URL = f"{base_url}?{'&'.join(params)}" if params else base_url
    engine_kwargs["connect_args"] = {
        # asyncpg passes unknown kwargs via server_settings; sslmode is
        # a libpq keyword handled by asyncpg's SSL negotiation.
        "ssl": True,  # enforce TLS (matches sslmode=require)
        "prepared_statement_cache_size": 0,  # PgBouncer compatibility (prepareThreshold=0)
        "server_settings": {
            "statement_timeout": "10000",  # kill runaway queries after 10 s
        },
    }

engine = create_async_engine(ACTIVE_DB_URL, **engine_kwargs)


# Enable Foreign Keys and WAL mode for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in type(dbapi_connection).__name__.lower() or isinstance(
        dbapi_connection, SQLite3Connection
    ):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-2000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    """Yield an async database session and ensure it is closed after use.

    Yields:
        AsyncSession: SQLAlchemy async session scoped to the current request.

    Raises:
        Exception: Re-raises any database exception after ensuring the session is closed.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def warmup_db() -> None:
    """Pre-warm the SQLAlchemy connection pool on startup.

    Runs a lightweight ``SELECT 1`` through every connection in the pool so
    Neon/PostgreSQL wakes up before the first real request arrives.  Safe to
    call once from the FastAPI ``lifespan`` or ``startup`` event.
    """
    if "sqlite" in ACTIVE_DB_URL:
        _db_logger.debug("[warmup_db] SQLite backend detected — skipping pool warm-up.")
        return

    from sqlalchemy import text

    pool_size = engine_kwargs.get("pool_size", 1)
    _db_logger.info("[warmup_db] Warming up %d DB connection(s)…", pool_size)
    tasks = []

    async def _ping() -> None:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))

    tasks = [_ping() for _ in range(pool_size)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    failures = [r for r in results if isinstance(r, Exception)]
    if failures:
        _db_logger.warning(
            "[warmup_db] %d/%d warm-up pings failed: %s",
            len(failures),
            len(tasks),
            failures[0],
        )
    else:
        _db_logger.info("[warmup_db] All %d connections warmed up successfully.", pool_size)

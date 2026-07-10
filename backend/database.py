import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
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

TURSO_URL        = os.getenv("TURSO_DATABASE_URL")       # e.g. libsql://my-db.turso.io
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")
LOCAL_DB_URL     = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./data/jobhunt_local.db")
REMOTE_PG_URL    = os.getenv("DATABASE_URL")             # kept for legacy / Postgres path

def _build_active_url() -> str:
    """Return the resolved async database URL at startup, logging the active backend."""
    if TURSO_URL:
        # libsql+aiosqlite over HTTPS — aiosqlite supports the libsql URL scheme
        # when the libsql-experimental package is installed.
        url = TURSO_URL.replace("libsql://", "sqlite+aiosqlite://")
        print(f"[DB] 🌐 Connecting to Turso edge database: {TURSO_URL}")
        return url
    if REMOTE_PG_URL:
        print("[DB] 🐘 Connecting to remote PostgreSQL.")
        return REMOTE_PG_URL
    print(f"[DB] 💾 Using local SQLite fallback: {LOCAL_DB_URL}")
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
    # PostgreSQL: production-hardened pool
    engine_kwargs.update({
        "pool_size":     20,    # baseline concurrent connections
        "max_overflow":  10,    # burst headroom
        "pool_recycle":  1800,  # recycle stale connections (seconds)
        "pool_timeout":  30,    # max wait for a free slot
        "pool_pre_ping": True,  # heartbeat before checkout
    })

engine = create_async_engine(ACTIVE_DB_URL, **engine_kwargs)

# Enable Foreign Keys and WAL mode for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in type(dbapi_connection).__name__.lower() or isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

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


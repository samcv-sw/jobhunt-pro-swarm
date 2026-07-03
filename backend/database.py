import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection

# Dual Database Pattern
# We use SQLite locally for zero-latency operations and WAL mode.
# Synchronization to remote Postgres will happen asynchronously via the Outbox table.

LOCAL_DB_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./jobhunt_local.db")
REMOTE_PG_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/jobhunt_pro")

engine = create_async_engine(
    LOCAL_DB_URL, 
    echo=False, 
    # Enable WAL mode for high concurrency
    execution_options={"isolation_level": "AUTOCOMMIT"}
)

# Enable Foreign Keys and WAL mode for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in type(dbapi_connection).__name__.lower() or isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

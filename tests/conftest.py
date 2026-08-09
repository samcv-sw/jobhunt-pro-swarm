import os
import sys

os.environ["TESTING"] = "1"
os.environ["PYTEST_RUNNING"] = "1"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from unittest.mock import MagicMock

import pytest
import pytest_asyncio

DB_PATH = "./data/jobhunt_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"
os.environ["TURSO_DATABASE_URL"] = ""

import contextlib

from backend.database import Base, engine
from backend.main import rate_limiter
from backend.tasks import celery_app


@pytest.fixture(autouse=True)
def mock_celery_send_task(monkeypatch):
    """Prevent Redis retry storm in tests: stub celery_app.send_task globally.

    Endpoints (trigger_scrape / trigger_cover_letter) ignore the return value and
    generate their own task_id, so a bare MagicMock is sufficient. Tests that need
    real timing behavior (e.g. test_backend_scraping_is_non_blocking) override this
    with their own monkeypatch.setattr inside the test body.
    """
    monkeypatch.setattr(celery_app, "send_task", lambda *args, **kwargs: MagicMock())
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_test_database_session():
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)

    # Dispose async engine if open to release file handles on Windows
    with contextlib.suppress(Exception):
        engine.dispose()

    # Remove old test DB if it exists to start fresh
    if os.path.exists(DB_PATH):
        with contextlib.suppress(Exception):
            os.remove(DB_PATH)
        with contextlib.suppress(Exception):
            if os.path.exists(f"{DB_PATH}-wal"):
                os.remove(f"{DB_PATH}-wal")
            if os.path.exists(f"{DB_PATH}-shm"):
                os.remove(f"{DB_PATH}-shm")

    # Run table creation synchronously with standard SQLite engine
    from sqlalchemy import create_engine
    sync_test_engine = create_engine(f"sqlite:///{DB_PATH}")
    try:
        Base.metadata.create_all(sync_test_engine, checkfirst=True)
    except Exception:
        pass
    sync_test_engine.dispose()


    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.commit()
    try:

        import web.app_v2 as app_v2
        if hasattr(app_v2, "_create_tables"):
            app_v2._create_tables(conn)
        elif hasattr(app_v2, "_create_core_tables"):
            app_v2._create_core_tables(conn)
            app_v2._create_campaign_tables(conn)
            app_v2._create_billing_tables(conn)
            app_v2._create_features_tables(conn)

        # Run DB migration scripts (e.g. translation tables)
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "db_migrations")
        if os.path.exists(migrations_dir):
            for sql_file in sorted(os.listdir(migrations_dir)):
                if sql_file.endswith(".sql"):
                    with open(os.path.join(migrations_dir, sql_file), "r", encoding="utf-8") as f:
                        with contextlib.suppress(Exception):
                            conn.executescript(f.read())
    finally:
        conn.close()

    yield

    # Clean up test DB after the session ends
    if os.path.exists(DB_PATH):
        with contextlib.suppress(Exception):
            os.remove(DB_PATH)



@pytest.fixture(autouse=True)
def reset_rate_limiter_global(request):
    is_rate_limit_test = (
        "rate_limiting" in request.node.name
        or "rate_limit" in request.node.name
        or "rate_limiter" in request.node.name
    )

    if not is_rate_limit_test:
        old_limit = rate_limiter.requests_limit
        rate_limiter.requests_limit = 100000

    rate_limiter.reset()
    yield
    rate_limiter.reset()

    if not is_rate_limit_test:
        rate_limiter.requests_limit = old_limit

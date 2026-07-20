import os
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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database_session():
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)

    # Remove old test DB if it exists to start fresh
    if os.path.exists(DB_PATH):
        with contextlib.suppress(Exception):
            os.remove(DB_PATH)

    # Run the table creation
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run the web app's custom table creation functions
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    try:
        from web.app_v2 import (
            _create_billing_tables,
            _create_campaign_tables,
            _create_core_tables,
            _create_features_tables,
        )

        _create_core_tables(conn)
        _create_campaign_tables(conn)
        _create_billing_tables(conn)
        _create_features_tables(conn)
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

import os

import pytest
import pytest_asyncio

DB_PATH = "./data/jobhunt_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"
os.environ["TURSO_DATABASE_URL"] = ""

import contextlib

from backend.database import Base, engine
from backend.main import rate_limiter


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

import asyncio
import time
import sys
import os
from unittest.mock import MagicMock, AsyncMock
import httpx
import pytest

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.main import app
from backend.auth import create_access_token
from backend.tasks import scrape_jobs, generate_cover_letter
from backend.sync_worker import sync_outbox_to_cloud
import backend.sync_worker

async def test_endpoint_authorization():
    print("--- Testing Endpoint Authorization ---")
    routes = [
        ("POST", "/api/v1/checkout", {"tier": "pro", "user_id": "test_user"}),
        ("POST", "/api/v1/scrape", {"user_id": "test_user", "target_urls": ["http://example.com"]}),
        ("POST", "/api/v1/generate-cover-letter", {"user_cv": "cv", "job_description": "job desc", "tone": "professional"}),
        ("POST", "/api/v1/ai/generate-cover-letter/stream", {"user_cv": "cv", "job_description": "job desc", "tone": "professional"}),
        ("POST", "/api/v1/accounts", {"tenant_id": "tenant123", "currency": "CREDITS", "balance_cents": 100}),
    ]
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for method, route, payload in routes:
            # 1. Missing Authorization header
            if method == "POST":
                resp = await client.post(route, json=payload)
            else:
                resp = await client.get(route)
            print(f"[{method}] {route} (No Auth) -> status: {resp.status_code}")
            assert resp.status_code == 401, f"{route} did not return 401 on missing auth. Got {resp.status_code}"
            
            # 2. Invalid Token
            headers = {"Authorization": "Bearer invalid_token_xyz"}
            if method == "POST":
                resp = await client.post(route, json=payload, headers=headers)
            else:
                resp = await client.get(route, headers=headers)
            print(f"[{method}] {route} (Invalid Token) -> status: {resp.status_code}")
            assert resp.status_code == 401, f"{route} did not return 401 on invalid token. Got {resp.status_code}"
            
            # 3. Expired Token
            expired_token = create_access_token({"sub": "test_user"}, expires_in=-10)
            headers = {"Authorization": f"Bearer {expired_token}"}
            if method == "POST":
                resp = await client.post(route, json=payload, headers=headers)
            else:
                resp = await client.get(route, headers=headers)
            print(f"[{method}] {route} (Expired Token) -> status: {resp.status_code}")
            assert resp.status_code == 401, f"{route} did not return 401 on expired token. Got {resp.status_code}"
            
    print("Endpoint Authorization Verification: PASSED\n")

async def test_concurrency_event_loop():
    print("--- Testing Event Loop Concurrency during Celery dispatch ---")
    
    # Mock delay call to simulate Redis network write latency (e.g. 100ms sleep)
    def slow_delay(*args, **kwargs):
        time.sleep(0.10)  # Blocking sleep on purpose
        mock_res = MagicMock()
        mock_res.id = "mocked-task-id-123"
        return mock_res
    
    # Backup original delay
    orig_delay = scrape_jobs.delay
    scrape_jobs.delay = slow_delay
    
    loop_responsiveness = []
    
    async def loop_monitor():
        for _ in range(50):
            start = time.perf_counter()
            await asyncio.sleep(0.005)
            delay = time.perf_counter() - start - 0.005
            loop_responsiveness.append(max(0.0, delay))
            
    # Start monitor task
    monitor_task = asyncio.create_task(loop_monitor())
    
    # Dispatches to FastAPI
    token = create_access_token({"sub": "authorized-user"})
    headers = {"Authorization": f"Bearer {token}"}
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        tasks = [
            client.post("/api/v1/scrape", json={"user_id": "test", "target_urls": ["http://test"]}, headers=headers)
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            assert r.status_code == 200, f"Expected 200 OK, got {r.status_code}"
            
    await monitor_task
    
    # Restore original delay
    scrape_jobs.delay = orig_delay
    
    max_delay = max(loop_responsiveness)
    print(f"Max event loop delay recorded: {max_delay * 1000:.2f} ms")
    assert max_delay < 0.05, f"Event loop was blocked for {max_delay * 1000:.2f} ms (> 50ms)"
    print("Event Loop Concurrency Verification: PASSED\n")

async def test_sync_worker_resilience():
    print("--- Testing Database Sync Worker Resilience ---")
    
    # Mock REMOTE_PG_URL so that raw_pg_url is set and not skipped
    orig_pg_url = backend.sync_worker.REMOTE_PG_URL
    backend.sync_worker.REMOTE_PG_URL = "postgresql://mock_user:mock_pass@mock_host:5432/mock_db"
    
    # Mock asyncio.sleep to fail/exit after a few iterations, or we mock it to raise an exception to stop the infinite loop.
    import asyncio as orig_asyncio
    orig_sleep_func = orig_asyncio.sleep
    
    sleep_count = 0
    class StopLoopException(Exception):
        pass
        
    async def mock_sleep(secs):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 3:
            raise StopLoopException("Intentional loop termination")
        await orig_sleep_func(0.001)  # fast sleep using original sleep
        
    # Mock asyncpg.connect to raise ConnectionError on first call, and generic Exception on second call
    connect_count = 0
    async def mock_connect(url):
        nonlocal connect_count
        connect_count += 1
        if connect_count == 1:
            raise ConnectionError("Mock Postgres Connection Failed")
        elif connect_count == 2:
            raise Exception("Mock Unexpected Database Panic")
        
        mock_conn = AsyncMock()
        mock_conn.is_closed = MagicMock(return_value=False)
        return mock_conn
        
    # Save original functions
    import asyncpg
    
    orig_connect = asyncpg.connect
    
    asyncpg.connect = mock_connect
    asyncio.sleep = mock_sleep
    
    try:
        await sync_outbox_to_cloud()
    except StopLoopException:
        print("Sync worker ran and loop was stopped after 3 iterations as planned.")
    except Exception as e:
        print(f"CRITICAL: Sync worker crashed with unexpected exception: {e}")
        raise e
    finally:
        # Restore original functions
        asyncpg.connect = orig_connect
        asyncio.sleep = orig_sleep_func
        backend.sync_worker.REMOTE_PG_URL = orig_pg_url
        
    assert connect_count >= 2, "Sync worker did not execute the expected loop cycles"
    print("Database Sync Worker Resilience Verification: PASSED\n")

async def main():
    try:
        await test_endpoint_authorization()
        await test_concurrency_event_loop()
        await test_sync_worker_resilience()
        print("ALL EMPIRICAL INTEGRITY TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"VERIFICATION FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

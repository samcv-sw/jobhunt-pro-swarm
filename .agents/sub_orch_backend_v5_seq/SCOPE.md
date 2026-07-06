# Scope: Backend Performance & DB Sync Hardening (Sequential)

## Overview
Optimize resource utilization across FastAPI endpoints, Celery workers, and async tasks to minimize event loop latency (<50ms delay) and improve SQLite/Postgres sync robustness.

## Requirements & Fixes
1. **Event Loop Latency**: In `backend/billing.py`, wrap the synchronous Stripe API call `stripe.checkout.Session.create` in `asyncio.to_thread` to prevent it from blocking the main FastAPI event loop.
2. **Sync Worker Resilience**: In `backend/sync_worker.py`:
   - Catch both `asyncpg.Error` and socket-level network errors (`OSError`) in the main loop to properly classify connection drops instead of logging them as "unexpected errors".
   - Differentiate connection drops during record writing from data failures. If a connection error occurs during the record push loop, break immediately to abort the batch and prevent endless identical logs.
   - Enclose the `cloud_conn.close()` command in `finally` with a try/except wrapper to ensure socket cleanup exceptions do not crash the daemon process.
   - Ensure soft error handling or dead-letter queuing to mitigate poison pill records.

## Complete Criteria
- Concurrency simulation tests pass with event loop latency < 30ms.
- Database sync worker unit and integration tests pass successfully, including connection drop simulation.

# plan.md - JobHunt Pro Cloud Optimization (Gen 2)

This document outlines the architecture, milestone decomposition, and interface contracts for implementing zero-investment, 24/7 cloud optimization features for JobHunt Pro.

## Architecture
- **FastAPI Core API (`backend/main.py`)**: Exposes health and management routes; routes incoming webhook requests; dispatches tasks.
- **SQLAlchemy DB Layer (`backend/database.py` & `core/database.py`)**: Connects to Neon PostgreSQL or local SQLite/Turso. Requires resilient connection pooling and recycling properties.
- **Celery Worker Configuration (`backend/celery_app.py` & `backend/tasks.py`)**: Processes heavy background tasks like scraping and AI letter generation. Needs memory recycling and rate-limiting throttling.
- **Local SQLite Queue / Outbox (`core/job_queue.py` & `backend/sync_worker.py`)**: Serves as a local queue to bypass Redis request limits, asynchronously syncing data up to Neon Postgres via `SyncOutbox`.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| 1 | M1: Free Tier Keep-Alive Scheduler | Expose `/api/v1/health` in `backend/main.py`. Implement background keep-alive ping loop in `start_cloud.py` (and a GitHub Actions cron config) to keep the Render free tier service active. | None | DONE |
| 2 | M2: DB Pool Recycling & Connection Warmer | Set `pool_recycle=280` and `pool_pre_ping=True` on SQLAlchemy async engines in `backend/database.py` and `core/database.py`. | None | DONE |
| 3 | M3: Groq Rate-Limit Controller & Fallbacks | Create a custom Celery rate-limiting task decorator/wrapper that reads Groq's response headers (`x-ratelimit-remaining`, `x-ratelimit-reset`) and dynamically delays tasks via exponential retries. | None | DONE |
| 4 | M4: Memory Reclamation and OOM Prevention | Set `worker_max_tasks_per_child=10` in `backend/celery_app.py` to recycle Celery child workers. Tune Python garbage collection in `start_cloud.py` (`gc.set_threshold`) to keep RSS under 450MB. | None | IN_PROGRESS |
| 5 | M5: Dual-Mode SQLite/Neon Job Dispatcher | Add a dual-mode dispatch toggle (`LOCAL_QUEUE_FALLBACK=1` or fallback on broker connection failure) to route high-frequency scrapes to the local SQLite job queue (`core/job_queue.py`), syncing results asynchronously to PG via `sync_worker.py`. | M2, M4 | PLANNED |

## Interface & Configuration Contracts

### 1. Keep-Alive Ping
- Endpoint: GET `/api/v1/health` -> `{"status": "ok"}`
- Daemon: Starts a daemon thread/process in `start_cloud.py` that checks the port or URL every 10 minutes.
- Cron Workflow: `.github/workflows/keep_alive.yml` executing curl against the public url every 10 minutes.

### 2. DB Pooling (SQLAlchemy)
- `create_async_engine(...)` parameters:
  - `pool_recycle=280`
  - `pool_pre_ping=True`

### 3. Groq Rate Limit Handler
- Celery task retry countdown:
  - Catch rate-limiting/API errors.
  - Parse headers from exception or API response.
  - Delay task using `self.retry(countdown=retry_seconds)`.

### 4. Celery & Python GC memory caps
- Celery config: `celery_app.conf.worker_max_tasks_per_child = 10`
- Python GC in `start_cloud.py`:
  ```python
  import gc
  gc.set_threshold(400, 5, 5) # Trigger more frequent collection
  # Or run a daemon thread that calls gc.collect() periodically
  ```

### 5. Dual-Mode Dispatcher
- Toggle: `os.getenv("LOCAL_QUEUE_FALLBACK")`
- Route: If enabled or if Redis/Celery broker connection fails, trigger local enqueue using `core.job_queue.enqueue_task("scrape_jobs", payload)`.
- Sync: Ensure local scraper updates trigger `SyncOutbox` inserts, which are pushed to Neon by `sync_worker.py`.

## Verification Checklist

### M1: Free Tier Keep-Alive
- GET `/api/v1/health` responds with `200 OK`.
- Keep-alive logs in `start_cloud.py` confirm periodic ping attempts.

### M2: DB Pool Recycling
- Verify that `backend/database.py` and `core/database.py` create async engines with `pool_recycle=280` and `pool_pre_ping=True`.

### M3: Groq Rate-Limit Controller
- Test with mock responses having rate limit headers. Task retries are scheduled with `countdown` matching the rate limit reset time.

### M4: Memory Reclamation
- Celery workers successfully exit and are replaced after 10 tasks.
- Garbage collection logs confirm active memory reclamation.

### M5: Dual-Mode Dispatcher
- Scrape tasks route to SQLite when Celery broker is offline or when `LOCAL_QUEUE_FALLBACK` is enabled.
- Pushed records sync to PostgreSQL successfully.

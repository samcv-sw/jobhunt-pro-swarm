# Project: JobHunt Pro Optimization Swarm

## Architecture
- **Frontend Layer**: Web templates located in `web/templates/` and their RTL variants in `web/templates/en/` (and local directories). Static stylesheets are in `web/static/css/`. Must strictly utilize CSS Logical Properties and render a premium glassmorphism theme with animations.
- **Backend API Layer**: FastAPI web server in `backend/main.py` routing asynchronous requests. Background task delegation via Celery/Redis queue in `backend/tasks.py` and `backend/celery_app.py`.
- **Database Layer**: Local SQLite database with WAL-mode (Wait-Ahead Log) enabled. State changes are serialized into a local Outbox table (`ps_crud_outbox` / `SyncOutbox` model).
- **Synchronization Layer**: Background sync worker in `backend/sync_worker.py` streaming local SQLite modifications to the remote PostgreSQL database.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | E2E Testing Suite | Design and implement an E2E testing suite (Tiers 1-4) verifying frontend, backend concurrency, and database sync. Write `TEST_READY.md`. | None | IN_PROGRESS (Conv ID: e55b2eca-ea77-43e7-abaa-6df4c9500e8f) |
| M2 | Frontend UI/UX Overhaul | Enforce strict CSS Logical Properties across static CSS sheets (`web/static/css/*.css`), apply premium glassmorphism theme, and optimize Arabic/RTL presentation. | None | IN_PROGRESS (Conv ID: d862a488-6582-4ff2-b029-8c5f6e3eff43) |
| M3 | Backend Concurrency Optimization | Refactor FastAPI (`backend/main.py`) and Celery/Redis configuration (`backend/celery_app.py`, `backend/tasks.py`) to prevent event-loop blocking on Celery calls. | None | IN_PROGRESS (Conv ID: 85146802-97a8-4bda-ba03-175341fb09cb) |
| M4 | Database WAL-mode & Outbox Sync | Implement local Outbox table populate logic and complete PostgreSQL sync in `backend/sync_worker.py` with sqlite WAL-mode configuration. | M3 | PLANNED |
| M5 | E2E Verification & Adversarial Hardening | Run the E2E test suite against the integrated system, pass 100% of tests, and complete Tier 5 adversarial coverage hardening. | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### FastAPI ↔ Celery Tasks (`backend/main.py` ↔ `backend/tasks.py`)
- FastAPI endpoints must invoke Celery tasks asynchronously using `.delay(...)` or `.apply_async(...)` without `await`ing their resolution.
- Celery task signatures:
  - `scrape_jobs.delay(target_urls: list[str], user_id: str) -> celery.result.AsyncResult`
  - `generate_cover_letter.delay(job_description: str, user_cv: str) -> celery.result.AsyncResult`
  - `send_application_email.delay(cover_letter_subject: str, cover_letter_body: str, recipient: str) -> celery.result.AsyncResult`

### Local Database ↔ Sync Outbox (`SyncOutbox` / `ps_crud_outbox`)
- Local SQLite database writes on critical entities (e.g. Accounts, Transactions, LedgerEntries) must record outbox entries.
- Outbox payload format:
  ```json
  {
    "id": "outbox_id",
    "table_name": "accounts|transactions|ledger_entries",
    "record_id": "stringified_primary_key",
    "operation": "INSERT|UPDATE|DELETE",
    "payload": { ...fields... },
    "created_at": "ISO-8601-timestamp",
    "synced": false
  }
  ```

### Sync Worker ↔ PostgreSQL Database (`backend/sync_worker.py` ↔ `Neon/PostgreSQL`)
- `sync_outbox_to_cloud()` polls `ps_crud_outbox` for `synced == False`.
- Stream payload changes to PostgreSQL. On successful transaction completion, mark `synced = True` in SQLite database.

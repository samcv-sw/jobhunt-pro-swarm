# Scope: JobHunt Pro E2E Testing

## Architecture
We are testing three main boundaries of the JobHunt Pro SaaS platform:
1. **Frontend UI/UX**: Next.js app in `frontend/` containing global styles (`globals.css`) and UI logic (`page.tsx`). Specifically verifying CSS Logical Properties (no physical directional styling), Arabic/RTL rendering/presentation support, and glassmorphism.
2. **Backend Concurrency**: FastAPI application in `backend/main.py` queueing tasks to Celery/Redis in a non-blocking manner.
3. **Database Sync Worker**: The SQLite database engine in WAL mode and the sync worker `backend/sync_worker.py` processing outbox records from `ps_crud_outbox`.

The E2E test suite will run using `pytest`. We will write:
- Frontend layout/styles static analysis and structure tests.
- FastAPI endpoint client tests (verifying task queueing does not block).
- Celery task configuration and routing tests.
- Database sync worker simulation tests.
- Multi-tier acceptance tests.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test Harness Initialization | Set up testing directory `tests/` and verify runner environment | None | IN_PROGRESS |
| 2 | Tier 1: Feature Coverage | Implement tests for CSS logical properties, glassmorphism, FastAPI queueing, and outbox syncing | M1 | IN_PROGRESS |
| 3 | Tier 2: Boundary & Edge Cases | Implement tests for inputs, errors, websocket lifecycle, retries, and batch processing | M2 | PLANNED |
| 4 | Tier 3: Cross-Feature Interaction | Implement integration tests verifying flow from FastAPI -> Celery -> DB Outbox -> Sync | M3 | PLANNED |
| 5 | Tier 4: Real-World Scenarios | Implement full E2E system flows, consistent hashing verification, and local-first offline syncing | M4 | PLANNED |
| 6 | Verification & TEST_READY | Run E2E test suite, ensure 100% pass, and publish `TEST_READY.md` | M5 | PLANNED |

## Interface Contracts
### FastAPI ↔ Celery (Redis)
- Endpoints: `POST /api/v1/scrape`, `POST /api/v1/generate-cover-letter`
- Queue routing: `scrape_jobs` -> `scraping` queue; `generate_cover_letter` -> `ai_inference` queue.
- Return format: `{"status": "queued", "task_id": "<celery-uuid>"}`

### SQLite ↔ Sync Worker
- Table: `ps_crud_outbox`
- Columns: `id` (int), `table_name` (str), `record_id` (str), `operation` (str), `payload` (JSON), `created_at` (datetime), `synced` (bool)
- Behavior: Sync worker fetches `synced == False`, updates status to `True` after syncing.

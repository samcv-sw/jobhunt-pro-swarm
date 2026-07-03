# Scope: Backend Concurrency, Database Sync & Security (R2 & R4)

## Architecture
- FastAPI app located in `backend/`
- DB synchronization script: `backend/sync_worker.py`
- Authentication module: `backend/auth.py` and `backend/main.py`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | FastAPI JWT Auth Protection | Protect all `/api/v1/*` endpoints with JWT Bearer auth | None | PLANNED |
| 2 | main loop Concurrency check | Guarantee FastAPI event loop remains responsive (< 50ms latency) | None | PLANNED |
| 3 | db sync resilience | Add `asyncpg.PostgresConnectionError` try/except retry in `sync_worker.py` | None | PLANNED |
| 4 | Verification & E2E backend tests | Verify backend/auth tests pass using pytest | M1, M2, M3 | PLANNED |

## Interface Contracts
- API requests to `/api/v1/*` without a valid JWT Bearer header must return `401 Unauthorized`.
- Celery task enqueueing must not block the FastAPI thread event loop for > 50ms.
- `sync_worker.py` should recover from postgres connection drops and retry.

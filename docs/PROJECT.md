# Project: JobHunt Pro Hardening (Maximum Overdrive - Optimization & Hardening Sweep)

## Architecture
- **Web App / API Layer**: FastAPI web server (`web/app_v2.py`, `backend/main.py`) handling JWT authentication, CSRF, and rate-limiting.
- **Task Queue / Worker Layer**: Celery worker integration (`backend/tasks.py`) performing asynchronous scraping and AI tailoring.
- **Stealth Scrapers**: Web/API scrapers with bypass fingerprinting and rotating IP tricks (`core/stealth.py`, `scrapers/stealth_ingest.py`).
- **Database Engine**: Local SQLite database synced with Neon PostgreSQL via PG/SQLite shim (`core/pg_sqlite_shim.py`, `backend/sync_worker.py`).
- **AI Core**: LLM providers pool matching resume keywords and cover letters (`core/ai_tailor.py`, `backend/ai_engine.py`).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | M1: Next.js Frontend | Refactor Next.js styles to use CSS Logical Properties and ensure build succeeds | None | DONE |
| 2 | M2: FastAPI & Celery Integration | Non-blocking Celery task dispatches and postgres error handling/reconnect in sync worker | None | DONE |
| 3 | M3: Stealth Ingest parsing | Ensure stealth_ingest.py parsing yields list[dict] with title and url keys | None | DONE |
| 4 | M4: JWT API Security | Protect all /api/v1/* endpoints with JWT Bearer validation | None | PLANNED |
| 5 | M5: CI/CD Test Validation | Fix RuntimeWarnings and ensure all 365+ tests and verify_integrity.py pass | None | PLANNED |
| 6 | M6: IMPROVE_ME.md Refactoring | Address remaining critical codebase-wide anomalies from IMPROVE_ME.md | None | PLANNED |

## Interface Contracts
### FastAPI App ↔ Database
- Queries pass through local SQLite and are translated dynamically for PostgreSQL under connection dropouts.
### FastAPI App ↔ Celery Worker
- Async tasks are dispatched to Redis/RabbitMQ queue without blocking FastAPI's event loop (<50ms delay).

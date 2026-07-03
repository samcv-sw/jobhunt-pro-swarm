# Project: JobHunt Pro Maximum Overdrive Optimization

## Architecture
JobHunt Pro consists of:
- **Frontend**: Next.js app in `frontend/` utilizing React, TailwindCSS. Needs strictly CSS logical properties and robust glassmorphism design.
- **FastAPI Backend**: Exposes REST endpoints, integrates JWT authentication, and schedules asynchronous scraping/AI tasks using Celery and Redis.
- **Celery/Redis Swarm**: Background task execution.
- **Database Layer**: SQLite (local WAL mode) with a synchronization worker (`sync_worker.py`) that propagates Outbox entries to Neon Postgres.
- **Scraper Layer**: `scrapers/stealth_ingest.py` with bypass capabilities.

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID | Directory |
|---|---|---|---|---|---|---|
| 1 | R1: Frontend RTL & Build | CSS Logical Properties, Glassmorphism, build check | None | IN_PROGRESS | 862ef450-8f92-46e3-9d1c-79f6656a295f | .agents/sub_orch_frontend_v5 |
| 2 | R2: Concurrency & Database Sync | FastAPI loop blocking <50ms, `sync_worker.py` Postgres resilience | None | IN_PROGRESS | e578e005-f5b0-41fa-888d-50849229c8a2 | .agents/sub_orch_backend_v5 |
| 3 | R3: Scraper Stealth | `stealth_ingest.py` anti-bot bypass & list[dict] formatting | None | IN_PROGRESS | 91d10ef2-c6c3-4f61-bb63-9c8e72579eeb | .agents/sub_orch_scraper_v5 |
| 4 | R4: JWT Auth Hardening | Protection of all `/api/v1/*` endpoints with JWT auth | None | IN_PROGRESS | e578e005-f5b0-41fa-888d-50849229c8a2 | .agents/sub_orch_backend_v5 |
| 5 | R5: E2E Test Suite Validation | Run and pass `pytest tests/e2e/` and verify E2E pipeline | M1, M2, M3, M4 | PLANNED | TBD | self |

## Interface Contracts
### FastAPI ↔ Celery
- Non-blocking task dispatch: FastAPI must use `delay()` or async tasks to dispatch to Celery without blocking the main event loop for > 50ms.
### Scraper ↔ API
- `stealth_ingest.py` should return `list[dict]` containing at minimum `title` and `url` keys.
### Auth Filter
- All `/api/v1/*` endpoints must validate HTTP `Authorization: Bearer <token>` and return `401 Unauthorized` on missing/invalid token.

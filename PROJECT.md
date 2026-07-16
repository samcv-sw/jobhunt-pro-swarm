# Project: JobHunt Pro Optimization

## Architecture
JobHunt Pro consists of:
1. **Frontend UI**:
   - 70+ Jinja2 HTML templates rendered by FastAPI (`web/templates/` and `web/templates/en/`).
   - A Next.js 16 Client-side application (`frontend/`).
2. **Backend Services**:
   - FastAPI server (`web/app_v2.py`) loading modular routers from `web/routers/`.
   - Dual Database Layer (`core/database.py` and `backend/database.py`) with support for PostgreSQL (remote) and SQLite (local fallbacks, e.g. `jobhunt_saas_v2.db`).
   - SQLite queries translation shim (`core/pg_sqlite_shim.py`).
3. **Test Suite**:
   - 608 Pytest test cases covering backend functionality, rate limiters, anti-ban features, payment processors, and E2E routes.

## Code Layout
- `web/templates/`: HTML Jinja2 templates (RTL/Arabic & LTR/English versions).
- `frontend/`: Next.js frontend source code (TypeScript, Tailwind, React 19).
- `web/routers/`: FastAPI router modules (e.g., `admin.py`, `dashboard.py`, `payments.py`, `public.py`).
- `backend/main.py`: Main FastAPI application entry point.
- `core/`: Core application modules, including database interfaces and pg/sqlite shim.
- `tests/`: Integration, unit, and performance tests (pytest).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | E2E Testing Track Setup | Inventory 608 tests, map to Tiers 1-4, publish `TEST_READY.md`. | None | PLANNED |
| M2 | Backend Router & DB Optimization | Optimize DLQ endpoint, Brevo/SendGrid webhooks, dashboard stats, query indices. | M1 | PLANNED |
| M3 | HTML Templates RTL & UI Overhaul | Polish all 70+ HTML templates in `web/templates/` for RTL/Arabic layout. | M1 | PLANNED |
| M4 | Next.js Frontend RTL Overhaul | Polish Next.js codebase, ensure clean production build. | M1 | PLANNED |
| M5 | Final E2E Test & Adversarial Hardening | Run all 608 tests, pass 100%, run Challenger adversarial tests (Tier 5), Audit. | M2, M3, M4 | PLANNED |

## Interface Contracts
### DLQ Requeue Endpoint (`/api/v1/admin/dlq/requeue`)
- Method: POST
- Request Body: JSON with specific queue name and optional task IDs.
- Response: Status of requeued tasks.

### Webhook Routers (Brevo & SendGrid)
- Endpoints: Process payload signatures, validate events, enqueue to DLQ on failure, update status.

### Dashboard Stats API (`/api/v1/dashboard/stats`)
- Optimization: Cache key queries, add SQL indices on frequently filtered fields (e.g., user_id, campaign_id, timestamp).

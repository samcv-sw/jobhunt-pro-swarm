# Scope: JobHunt Pro Cloud Stealth & Reliability Hardening

## Architecture
- **Frontend Layer**: Static assets built from `frontend/` and served via Cloudflare Pages. API requests `/api/v1/*` proxied to Render.
- **Backend API Layer**: FastAPI container running on Render (Free Tier). DB queries executed via PgBouncer pooled connections.
- **Background Worker Layer**: Celery/Background workers managed with memory guards (`--max-tasks-per-child`, `--max-memory-per-child`).
- **Data Sync Layer**: SQLite to Neon PostgreSQL sync via Outbox pattern worker (`sync_worker.py`).
- **Stealth Scraper Layer**: Scrapers utilizing a dynamic free proxy pool harvested hourly by `core/ghost_hunter.py`.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|-------------|--------|
| 1 | Cloudflare Pages Next.js Deployment | Configure static Next.js build and routing (`_redirects`/`vercel.json`) to Render backend. Update allowed CORS origins in backend config. | none | PLANNED |
| 2 | GitHub Actions Keep-Alive | Set up `.github/workflows/keepalive.yml` triggering every 12 minutes to warm Render and Neon DB. | none | PLANNED |
| 3 | Celery Memory Guard | Configure memory ceilings and recycling options in `start_cloud.py` for supervisor. | none | PLANNED |
| 4 | Neon PgBouncer connection updates | Append query parameters and route port 5432 to enable PgBouncer in `backend/database.py` and `backend/sync_worker.py`. | none | PLANNED |
| 5 | Free Proxy Pool Scraper Rotation | Create proxy scraper task in `core/ghost_hunter.py` and rotate in Playwright/Camoufox Stealth scraper. | none | PLANNED |
| 6 | Verification & Tests | Run all 403 test suites via pytest to ensure zero regression. | 1, 2, 3, 4, 5 | PLANNED |

## Interface Contracts
- **CORS configuration**: Allowed origins dynamically loaded/configured in `backend/config.py` (which maps to root `config.py`) or `backend/main.py` including the Cloudflare Pages subdomain wildcard/exact domains.
- **Proxy rotation**: `core/ghost_hunter.py` exposes validated proxies list or saves to a cache/database for stealth scraper to consume.

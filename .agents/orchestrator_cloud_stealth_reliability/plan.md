# Plan: JobHunt Pro Cloud Stealth & Reliability Hardening

## Overview
This plan implements 0-cost, 24/7 permanent cloud deployment optimizations, performance updates, and reliability enhancements for the JobHunt Pro platform.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Cloudflare Pages Next.js Deployment | Configure Next.js frontend deployment files for Cloudflare Pages; set up proxy routing (`vercel.json`/redirects) to Render; update CORS origins in `backend/config.py` | None | PLANNED |
| 2 | GitHub Actions Keep-Alive | Create `.github/workflows/keepalive.yml` to trigger every 12 minutes to ping `/healthz` on Render backend and database warming endpoint | None | PLANNED |
| 3 | Celery Memory Guard | Configure `--max-tasks-per-child=10` and `--max-memory-per-child=150000` in `start_cloud.py` | None | PLANNED |
| 4 | Neon PgBouncer updates | Update `backend/database.py` and `backend/sync_worker.py` connection URLs to append `?sslmode=require&prepareThreshold=0` | None | PLANNED |
| 5 | Free Proxy Pool Rotation | Implement proxy scraper in `core/ghost_hunter.py` to scrape free proxy list hourly, validate and rotate in scrapers | None | PLANNED |
| 6 | Verification & Tests | Run E2E and Unit test suites (`python -m pytest tests/ -q`) to ensure all 403 test suites pass | M1, M2, M3, M4, M5 | PLANNED |

## Interface Contracts
- **CORS configuration**: Allowed origins dynamically loaded/configured in `backend/config.py` including the Cloudflare Pages subdomain wildcard/exact domains.
- **Proxy rotation**: `core/ghost_hunter.py` exposes validated proxies list or saves to a cache/database for stealth scraper to consume.

## Code Layout
- Frontend build: `frontend/`
- Workflows: `.github/workflows/`
- App entrypoints & db config: `backend/database.py`, `backend/sync_worker.py`, `backend/config.py`, `start_cloud.py`
- Core scraper/stealth logic: `core/ghost_hunter.py`, scrapers/stealth config

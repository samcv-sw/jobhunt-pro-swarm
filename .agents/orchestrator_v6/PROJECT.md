# Project: JobHunt Pro System Optimization

## Architecture
- **Backend (Python)**: FastAPI application serving API routes (`web/app.py` / `web/app_v2.py` / `backend/main.py`), Celery/Queue workers (`core/campaign_runner.py`, `core/email_engine.py`, `core/pa_job_scraper.py`), and utility modules (`core/ai_tailor.py`, `core/ats_matcher.py`).
- **Frontend (Next.js)**: modern dashboard view in `frontend/src/app/` served locally.
- **Scraping Engine**: python scripts in `scrapers/stealth_ingest.py` for headless/stealth scraping.
- **Database**: SQLite / PostgreSQL with connections managed by async clients or SQLite pools.

## Code Layout
- `core/`: Core business logic, ATS, AI, and worker runners.
- `web/`: Legacy python-based web server and templates.
- `backend/`: FastAPI backend for API routes.
- `frontend/`: Next.js web application.
- `scrapers/`: Stealth scraping modules.
- `tests/`: Automated test suite containing unit and E2E tests.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Audit & Scaffolding | Run tests, identify file issues, and create workspace folders | None | DONE |
| 2 | Backend & AI Scrapers | Optimize database, connection pooling, and AI/scrapers | M1 | DONE |
| 3 | Frontend Overhaul | Glassmorphism UI, logical CSS properties, Arabic RTL support | M1 | DONE |
| 4 | Verification & Audit | E2E test runs, reviewer validation, and forensic audits | M2, M3 | IN_PROGRESS (IDs: f763c902, a782af2a, 64e2dab8, 8766d764, 0f2ff5d9) |

## Interface Contracts
### Backend API ↔ Frontend
- Authentication: Bearer JWT in `Authorization` headers.
- `/api/v1/dashboard/metrics`: yields system performance stats (concurrency-safe).
- `/api/v1/scraper/start`: POST request triggering async scrape task, returns status.

# Project: JobHunt Pro Overdrive Run 4 (gen5)

## Architecture
JobHunt Pro comprises:
- **FastAPI Backend**: Orchestrates API requests, user auth, and scraping campaigns.
- **Next.js Frontend**: Premium dashboard view for users, with Arabic/RTL support and modern glassmorphism UI.
- **Celery Workers**: Handles heavy background processing tasks like job scraping and AI tailored email generation.
- **SQLite Database**: Local-first storage using WAL mode and Outbox pattern, with a synchronization worker (`sync_worker.py`) to replicate to a remote PostgreSQL DB.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Cloud DB Sync & Performance | Verify and optimize database queries and synchronization between the local SQLite database and the remote Neon PostgreSQL database (`DATABASE_URL`), ensuring zero data loss and minimal synchronization latency. | None | DONE |
| 2 | Production Security & Sessions | Verify that all API and WebSocket endpoints on the production site strictly enforce rate limits and require valid JWT Bearer tokens. Verify that sessions and cookie data stored in the database are encrypted and protected. | None | DONE |
| 3 | Scraper Stealth & Ingestion | Ensure the scraper engine is completely stealthy and resilient to bot-detection on the production site, returning correctly structured listings containing `title` and `url` keys. | None | DONE |
| 4 | Production Build & CSS Logical | Ensure the production Next.js application compiles cleanly and maintains 100% compliance with CSS Logical Properties, utilizing premium glassmorphism styles and Cairo/Tajawal fonts. | None | DONE |
| 5 | Complete Test Suite & Audit | Run the entire testing suite (`tests/`) and perform challenger/reviewer/auditor checks on the production code. | M1, M2, M3, M4 | IN_PROGRESS |

## Interface Contracts
- **Scraper Ingestion**: The scraper engine `scrapers/stealth_ingest.py` must return a list of dictionaries where each dict has at least `title` (str) and `url` (str) keys.
- **API Authentication**: All API endpoints under `/api/v1/*` must require a valid JWT bearer token. Unauthorized calls must return a `401 Unauthorized` status.
- **Frontend Stylesheets**: CSS logical properties must be strictly used. Zero instances of physical properties (`margin-left`, `margin-right`, `padding-left`, `padding-right`, `left`, `right`) are allowed in stylesheets/templates inside `frontend/src/`.

# Project plan.md — JobHunt Pro Overdrive Run 3

## Architecture
JobHunt Pro comprises:
- **FastAPI Backend**: Orchestrates API requests, user auth, and scraping campaigns.
- **Next.js Frontend**: Premium dashboard view for users, with Arabic/RTL support and modern glassmorphism UI.
- **Celery Workers**: Handles heavy background processing tasks like job scraping and AI tailored email generation.
- **SQLite Database**: Local-first storage using WAL mode and Outbox pattern, with a synchronization worker (`sync_worker.py`) to replicate to a remote PostgreSQL DB.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Backend Performance & Sync | Optimize event loop (<50ms latency), DB worker reconnect & retry. | None | DONE |
| 2 | Frontend UI/UX & RTL Polish | Audit physical CSS properties, check Next.js build, verify glassmorphism. | None | DONE |
| 3 | Scraper Stealth & Parsing | Audit anti-bot bypass & ensure structured dictionary returns (`title`, `url`). | None | DONE |
| 4 | Security & Auth | Audit endpoints for JWT verification & rate-limiting. | None | DONE |
| 5 | Full Test Suite & Audit | Run entire test suite and forensic integrity audits. | M1, M2, M3, M4 | DONE |

## Interface Contracts
- **Scraper Ingestion**: The scraper engine `scrapers/stealth_ingest.py` must return a list of dictionaries where each dict has at least `title` (str) and `url` (str) keys.
- **API Authentication**: All API endpoints under `/api/v1/*` must require a valid JWT bearer token. Unauthorized calls must return a `401 Unauthorized` status.
- **Frontend Stylesheets**: CSS logical properties must be strictly used. Zero instances of physical properties (`margin-left`, `margin-right`, `padding-left`, `padding-right`, `left`, `right`) are allowed in stylesheets/templates inside `frontend/src/`.

# Project: JobHunt Pro Optimization and Modernization

## Architecture
JobHunt Pro comprises two distinct application stacks in the same repository:
1. **PythonAnywhere Flask Stack**:
   - Backend logic: `core/` (`campaign_runner.py`, `email_engine.py`, `multi_source_scraper.py`, `pa_job_scraper.py`, `ai_tailor.py`, `ats_matcher.py`)
   - Web application & views: `web/`
   - UI templates: `templates/` (Flask templates)
   - Configuration: `config.py`
   - Scheduler & runner: `orchestrator.py`
   - Tests: `tests/` (excluding `tests/e2e/`)
2. **FastAPI & Next.js Stack**:
   - Backend API: `backend/` (FastAPI app with JWT, Celery tasks, etc.)
   - Frontend web client: `frontend/` (Next.js project)
   - Scrapers: `scrapers/` (stealth scraping ingesters)
   - E2E tests: `tests/e2e/`

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID |
|---|------|-------|-------------|--------|-----------------|
| 1 | Exploration & Diagnosis | Run existing test suites, evaluate all files, identify bug details and security issues | None | DONE | c3145e36-f27a-4e22-8e6e-f819549712d3 |
| 2 | FastAPI & Next.js Stack | R1-R5 of follow-up request (Groq streaming, Next.js dashboard, stealth bypass, JWT, E2E tests) | M1 | DONE | 68273ac7-fd8e-470f-a58b-0f4ffe9f16fc |
| 3 | Flask Stack: Quality & Security | R1, R3, R4, R5 of initial request (core backend fixes, tests, performance, security audit) | M1 | IN_PROGRESS | b26e0bb4-6e46-4487-95e6-3ff3c1f3c12b |
| 4 | Flask Stack: UI/UX overhaul | R2 of initial request (web/templates/ styling, logical properties, Arabic typography, responsiveness) | M3 | PLANNED | TBD |
| 5 | Codebase Cleanup & Archive | R6 of initial request (moving backups to archive/, script consolidation, hash duplicates removal) | M3, M4 | PLANNED | TBD |

## Interface Contracts
- **FastAPI Auth & Scrape**:
  - GET/POST `/api/v1/scrape` requires `Authorization: Bearer <JWT_TOKEN>`.
  - POST `/api/v1/ai/generate-cover-letter/stream` streams SSE events.
- **SQLite Database**:
  - Wal mode must be enabled: `PRAGMA journal_mode = wal;` and foreign keys enabled: `PRAGMA foreign_keys = ON;`.
  - Anti-ban checks (`can_apply_to_company`) must run in ≤ 1 DB round-trip.

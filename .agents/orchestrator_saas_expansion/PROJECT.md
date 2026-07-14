# Project: JobHunt Pro SaaS Expansion & Migration

## Architecture
- **Web App / API Layer**: FastAPI web server (`web/app_v2.py`, `backend/main.py`) handling JWT, CORS, rate limiting, and OAuth login.
- **Task Queue / Worker Layer**: Celery worker (`backend/tasks.py`, `backend/sync_worker.py`) for email dispatch, scraping, and NLP job matching.
- **Stealth Scrapers**: Web/API scrapers using Playwright, Camoufox, and HTTP bypass.
- **Database Engine**: Local SQLite database synced with Neon PostgreSQL / Turso remote.
- **AI Core**: LLM providers pool, AraBERT embeddings, and PDF parsers.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| 1 | M1: Backend Code Quality, Refactoring & Security | IMP-154 (vulture), IMP-158 (decomposition), IMP-160 (isort), IMP-162 (pip freeze), IMP-190 (LinkedIn OAuth), R2 (Auto-fill browser agent) | None | IN_PROGRESS (Conv: 4ec5c82c-33ff-44a2-84ce-3126969d04ad) |
| 2 | M2: Backend Concurrency, Database & NLP | IMP-034 (N+1 query audit), IMP-039 (Celery chords), IMP-183 (AraBERT matching), IMP-247 (pdfplumber) | None | IN_PROGRESS (Conv: 3e49a746-5cea-4b7e-9423-69f0eab49048) |
| 3 | M3: Frontend Improvements & Onboarding | IMP-037 (bundle analysis), IMP-038 (Next.js ISR), IMP-187 (onboarding wizard), IMP-243 (streaming cover letter), IMP-101 (Jest snapshots) | None | IN_PROGRESS (Conv: 868ca858-dfcb-4c6b-90bd-814bc039a80e) |
| 4 | M4: Cloud & Routing Hardening | IMP-128 (DNS failover) | None | IN_PROGRESS (Conv: 4c2670f0-c5a8-4926-8b41-00ecf8d7e934) |
| 5 | M5: Testing, Audits & Verification | IMP-095 (SMTP E2E), IMP-097 (Telegram bot tests), IMP-099 (Locust), IMP-100 (mutmut), IMP-102 (Schemathesis), Victory Audit | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Auto-Fill Browser Agent
- File: `core/form_autofill.py`
- Signature: `autofill_job_form(url: str, user_profile: dict) -> dict`
- Response: `{success: bool, screenshot_path: str}` or error structure.

### AraBERT Job Matching
- File: `core/ats_matcher.py` or new NLP helper
- Matches Arabic jobs using Morphological AraBERT embeddings.

### LinkedIn OAuth2
- Auth endpoint `/api/v1/auth/linkedin` utilizing `authlib` to retrieve user profile and import to CV.

# BRIEFING — 2026-07-12T13:21:13+03:00

## Mission
Analyze the codebase for Cloudflare Pages Next.js deployment, GitHub Actions Keep-Alive, Celery Memory Guard, Neon PgBouncer connection strings, and free proxy pool scraper rotation.

## 🔒 My Identity
- Archetype: Teamwork Explorer (Explorer 1)
- Roles: Read-only investigator, analyzer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1
- Original parent: 6ecf45d6-6d9d-4904-a199-48bb6826dede
- Milestone: Milestone 1: Multi-Key JWT Secret Rotation

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Code only mode (no external network requests, only codebase analysis)
- Never use placeholder code in report recommendations

## Current Parent
- Conversation ID: d42acd51-edc2-4ee9-91ee-6661881fc368
- Updated: 2026-07-12T13:21:13+03:00

## Investigation State
- **Explored paths**:
  - `frontend/` (Next.js frontend setup and config)
  - `cloudflare/pages/` (Cloudflare Pages workers / _worker.js routing)
  - `backend/main.py` (CORS loading and health endpoints)
  - `.github/workflows/` (keepalive yml files)
  - `start_cloud.py` (Celery command construction)
  - `backend/database.py` (SQLAlchemy / asyncpg database connection and pooling parameters)
  - `backend/sync_worker.py` (asyncpg raw connection to Neon)
  - `core/ghost_hunter.py` (Camoufox public scraper loop)
- **Key findings**:
  - Static Next.js export routes via `cloudflare/pages/_worker.js` and allows proxying `/api` paths.
  - Render spins down in 15 minutes, Neon database in 5 minutes; keeping them warm requires hitting database-querying detailed health endpoints (`/api/v1/health/detailed`) or running local `neon_warmer.py` script.
  - Celery process-recycling arguments `--max-tasks-per-child` and `--max-memory-per-child` only work with child-process prefork pool on Linux.
  - PgBouncer transaction pooling conflicts with prepared statements in asyncpg; statement caches must be disabled by setting `statement_cache_size=0`. Raw asyncpg rejects JDBC parameters like `prepareThreshold`, so custom parameters must be configured via connection arguments rather than URL queries.
  - Camoufox can run in rotated mode by scraping free proxies hourly (using free-proxy-list.net) and creating a separate browser context per request.
- **Unexplored areas**: None. All requested areas have been fully explored and designed.

## Key Decisions Made
- Chose to resolve PgBouncer prepared statement conflict by stripping parameters from URL and applying driver-level `statement_cache_size=0` configurations.
- Recommended lazy DB check in `ghost_hunter.py` to conserve memory and CPU before launching the Playwright browser.
- Suggested dual-ping keepalive workflow for robust Render & Neon DB warming.

## Artifact Index
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1\ORIGINAL_REQUEST.md` — Record of original and new requests.
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1\analysis.md` — Current milestone analysis report.
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1\progress.md` — Liveness and step tracking.

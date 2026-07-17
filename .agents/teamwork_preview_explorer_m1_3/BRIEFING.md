# BRIEFING — 2026-07-16T20:32:00+03:00

## Mission
Analyze PythonAnywhere compatibility, core endpoint performance/timeout risks, auth rate limits, scraper anti-ban headers, and run baseline pytest.

## 🔒 My Identity
- Archetype: explorer
- Roles: read-only investigator
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3
- Original parent: 78a73b8e-5c44-4f6a-821d-6c013b3e5512
- Milestone: m1_3

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze backend routers and main entry point for PythonAnywhere restricted environment compatibility
- Investigate speed of core endpoints for timeout risks
- Inspect auth rate limits and scraper anti-ban headers
- Execute test suite using `uv run pytest` for baseline

## Current Parent
- Conversation ID: 78a73b8e-5c44-4f6a-821d-6c013b3e5512
- Updated: 2026-07-16T20:32:00+03:00

## Investigation State
- **Explored paths**: `backend/main.py`, `web/app_v2.py`, `web/routers/dashboard.py`, `backend/routers/admin.py`, `web/routers/admin.py`, `web/routers/auth.py`, `web/routers/jobs.py`, `core/pg_sqlite_shim.py`, `core/aegis_shield.py`, `core/iron_cloak.py`, `core/anti_ban.py`, `core/pa_job_scraper.py`, `infra/init.sql`
- **Key findings**:
  - Ephemeral background tasks inside ASGI lifespan will be terminated unexpectedly on uWSGI process recycle.
  - Thread pool sizes (32 workers) are too high for PythonAnywhere thread limits.
  - Synchronous Upstash REST API requests in rate limiting add massive latency and timeout risks.
  - SQLite `DELETE` mode on NFS blocks write concurrency, causing thread blockages and slow dashboard stats / DLQ requeues.
  - Rate limiting writes to database (`system_config` table) on every authentication check, causing database lockups.
  - Scraper fallback to `urllib` cannot spoof TLS fingerprints and will get blocked.
  - All 632 test cases pass in 188.84 seconds.
- **Unexplored areas**: None (task completed).

## Key Decisions Made
- Executed full test suite locally inside the repo using `uv run pytest`.
- Documented findings in `analysis.md` and `handoff.md`.

## Artifact Index
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\analysis.md` — Compatibility analysis and baseline test report.
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\handoff.md` — Handoff report.

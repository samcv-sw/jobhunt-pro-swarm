# BRIEFING — 2026-07-12T13:21:13+03:00

## Mission
Analyze codebase for Cloudflare Pages deployment, GitHub keep-alive workflow, Celery memory guard, Neon PgBouncer configuration, and free proxy scraper rotation.

## 🔒 My Identity
- Archetype: explorer
- Roles: Teamwork explorer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_2
- Original parent: d42acd51-edc2-4ee9-91ee-6661881fc368
- Milestone: Milestone 1 & 2 Preview Analysis

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze Next.js Cloudflare Pages, GitHub Keepalive, Celery worker constraints, Neon PgBouncer connection params, and Proxy rotation in ghost_hunter.py.

## Current Parent
- Conversation ID: d42acd51-edc2-4ee9-91ee-6661881fc368
- Updated: 2026-07-12T13:21:13+03:00

## Investigation State
- **Explored paths**:
  - `frontend/` (Next.js configurations, package.json, _worker.js routing proxy)
  - `.github/workflows/` (keep-alive workflows)
  - `start_cloud.py` (supervisor starting Celery worker and memory watchdogs)
  - `backend/database.py` (database session and connection parameters for PostgreSQL)
  - `backend/sync_worker.py` (outbox sync connection using asyncpg)
  - `core/ghost_hunter.py` (Camoufox job description scraper)
- **Key findings**:
  - Cloudflare Pages serves Next.js static output via `_worker.js` proxy routing.
  - Celery prefork workers on Linux can be constrained via command-line arguments.
  - Neon PgBouncer connections require disabling prepared statements. Direct param appends fail in `asyncpg` DSNs.
  - Proxy rotation in Camoufox requires hourly scraping from `free-proxy-list.net` and connection exception eviction.
- **Unexplored areas**: None.

## Key Decisions Made
- Performed detailed static analysis of all five areas.
- Proposed clean python-level parameter extractions for database connection parameters to bypass `asyncpg` limits.
- Structured a self-healing retry block for the Camoufox proxy.

## Artifact Index
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_2\analysis.md` — Complete analysis report of Milestones 1 to 5.

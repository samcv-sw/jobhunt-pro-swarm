# BRIEFING — 2026-07-12T13:21:13+03:00

## Mission
Analyze the codebase for Cloudflare Pages Next.js, GitHub Actions Keep-Alive, Celery Memory Guard, Neon PgBouncer, and Free Proxy Pool Scraper rotation.

## 🔒 My Identity
- Archetype: Teamwork explorer (Read-only investigation)
- Roles: Investigator, Synthesizer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3
- Original parent: d42acd51-edc2-4ee9-91ee-6661881fc368
- Milestone: Milestones 1 to 5 Analysis

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- CODE_ONLY network mode
- Write analysis report to c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\analysis.md
- Produce handoff.md in working directory

## Current Parent
- Conversation ID: d42acd51-edc2-4ee9-91ee-6661881fc368
- Updated: 2026-07-12T13:21:13+03:00

## Investigation State
- **Explored paths**:
  - `frontend/package.json`, `frontend/next.config.ts`, `vercel.json`, `cloudflare/wrangler.toml`
  - `backend/main.py`, `config.py`
  - `.github/workflows/keep-alive.yml`, `.github/workflows/keep_alive.yml`, `core/neon_warmer.py`
  - `start_cloud.py`, `backend/celery_app.py`, `backend/tasks.py`
  - `backend/database.py`, `backend/sync_worker.py`
  - `core/ghost_hunter.py`
- **Key findings**:
  - Frontend is Next.js with SSG (`output: "export"`), built using `npm run build` outputting to `frontend/out/`. Redirects and headers on Cloudflare Pages should be placed in `frontend/public/_redirects` and `frontend/public/_headers` (since they copy directly to `out/`).
  - Backend CORS allowed origins are loaded from the environment variable `ALLOWED_ORIGINS` in `backend/main.py`. Wildcards are resolved by `SecureCORSMiddleware`.
  - Keep-alive can run `core/neon_warmer.py` directly (using GitHub Actions secrets) or ping `/api/v1/health/detailed` to keep the Neon DB connection warm.
  - Celery is run as a subprocess in `start_cloud.py` using `sys.executable -m celery`. Adding `--max-tasks-per-child=10` and `--max-memory-per-child=150000` requires appending these to `celery_cmd`. These properties are also set in `backend/celery_app.py`.
  - Neon PgBouncer connection strings can be configured by parsing `REMOTE_PG_URL` in `database.py`, adding `-pooler` to the host, forcing port 5432, and appending `?sslmode=require&prepareThreshold=0` (or `&prepareThreshold=0` if `?` exists).
  - Proxy scraping in `ghost_hunter.py` can be done via a custom utility function targeting public proxy sites, utilizing an hourly file-based cache (`data/proxy_cache.json`) and recreation of the Camoufox browser on proxy failure.
- **Unexplored areas**: None.

## Key Decisions Made
- Maintain strict segregation of roles.
- Follow read-only investigation constraint without making codebase changes.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\analysis.md — Main Analysis Report
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\handoff.md — Handoff Report

# BRIEFING — 2026-07-12T13:32:15Z

## Mission
Investigate the codebase and recommend how to configure a lightweight GitHub Actions workflow (run every 30 minutes) to execute the scraping and applying loop.

## 🔒 My Identity
- Archetype: Teamwork Explorer
- Roles: Read-only investigator
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_hf_2
- Original parent: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Milestone: Milestone 2: GitHub Actions Scheduled Runner Cron

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- CODE_ONLY network mode: no external requests, use only local searches
- Follow Teamwork explorer protocol

## Current Parent
- Conversation ID: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Updated: 2026-07-12T13:32:15Z

## Investigation State
- **Explored paths**:
  - `.github/workflows/` (workflows: `auto_apply.yml`, `job-hunt.yml`, `kronos_cloud.yml`, `smart-tick.yml`, `pa_watchdog.yml`)
  - `backend/` (`sync_worker.py`, `main.py`)
  - `core/` (`worker.py`, `queue_worker.py`, `job_queue.py`, `campaign_runner.py`, `multi_tenant.py`, `pg_sqlite_shim.py`)
  - `web/` (`cron_trigger.py`, `cloud_tick_router.py`, `app.py`, `app_v2.py`)
  - `tests/` (`test_multi_tenant.py`)
- **Key findings**:
  - `web/cron_trigger.py` is the designated CLI script for Scheduled Tasks that runs the full multi-tenant job cycle (`Search → Apply → Follow-up`) using `MultiTenantRunner`.
  - The API endpoint `/api/v2/worker/tick` (in `web/app.py`) processes queued tasks, but is restricted by HTTP timeouts and server process limits.
  - Matrix scrapers are executed concurrently via `scripts/run_all_scrapers.py` (which routes requests through a Cloudflare Worker scraper via `core/matrix_scrape_handler.py`).
  - No script named `run_once.py` exists in the repository, making it a legacy reference in `job-hunt.yml`.
- **Unexplored areas**: None

## Key Decisions Made
- Recommending direct CLI execution of `web/cron_trigger.py` in GHA rather than HTTP-based API trigger, due to execution timeouts and server constraints.
- Documented setup instructions and required environment secrets.

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_hf_2\handoff.md — Final investigation report

# BRIEFING — 2026-07-12T16:31:00+03:00

## Mission
Investigate codebase and recommend how to implement Milestone 2 (GitHub Actions Scheduled Runner Cron).

## 🔒 My Identity
- Archetype: explorer
- Roles: Read-only investigation, analyze problems, synthesize findings, produce structured reports
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_hf_1
- Original parent: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Milestone: Milestone 2: GitHub Actions Scheduled Runner Cron

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- CODE_ONLY network mode: no external web access, no curl/wget to external URLs

## Current Parent
- Conversation ID: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Updated: 2026-07-12T16:31:00+03:00

## Investigation State
- **Explored paths**: 
  - `.github/workflows/` (auto_apply.yml, job-hunt.yml, kronos_cloud.yml, smart-tick.yml, keepalive.yml, pa-autorenew.yml)
  - `backend/` (celery_app.py, sync_worker.py, tasks.py, main.py)
  - `core/` (campaign_runner.py, queue_worker.py, job_queue.py, lightning_runner.py)
  - `web/` (app.py, app_v2.py)
  - `scripts/` (run_all_scrapers.py, playwright_ai_apply.py, force_rita_campaign.py)
- **Key findings**:
  - Found 17 workflows. `smart-tick.yml` ticks `/api/v2/worker/tick` on PythonAnywhere every 5 mins. `auto_apply.yml` runs a Playwright typescript bot. `kronos_cloud.yml` runs scrapers concurrently and runs outreach engines every 6 hours. `job-hunt.yml` tries to run a missing `run_once.py`.
  - Scraping & applying are coupled inside `core/campaign_runner.py` via `run_campaign` which uses `PAJobScraper` (JSearch + LinkedIn XHR) and `EmailEngine`/`micro_smtp`.
  - Identified `core/queue_worker.py` as the background queue listener (`while True`) and `backend/sync_worker.py` as the DB sync loop.
  - Identified that `/api/cron/tick` in `web/app_v2.py` fails when spawning `run_campaign_cli.py` in the background because the file is missing from the workspace.
- **Unexplored areas**: None.

## Key Decisions Made
- Propose two deployment strategies: a serverless GHA runner cron using a new `run_queue_tick_once.py` script, or an API-driven cron using curl to hit the web app.
- Recommend creating the missing `run_campaign_cli.py` and `run_once.py` scripts to prevent runtime failures in existing flows.

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_hf_1\handoff.md — Handoff report with findings and recommendations

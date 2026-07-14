# Handoff Report - Milestone 2: GitHub Actions Scheduled Runner Cron

This report details the investigation of the existing GitHub workflows and scheduled runner commands in the codebase, and proposes recommendations to implement Milestone 2.

## 1. Observation

During the codebase investigation, the following files and codes were observed:

### A. Existing GitHub Workflows (`.github/workflows/`)
There are **17 workflow files** in `.github/workflows/`. The automation/scheduler-relevant ones are:
1. **`smart-tick.yml`**: Runs every 5 minutes (`*/5 * * * *`). It performs a HTTP POST trigger to the PythonAnywhere web app:
   ```yaml
   RESPONSE=$(curl -s --max-time 300 \
     -X POST "${PA_URL}/api/v2/worker/tick" \
     -H "Content-Type: application/json" \
     -d '{"source":"gh-actions-cron"}' || echo '{"processed":0,"errors":["curl_failed"]}')
   ```
2. **`auto_apply.yml`**: Runs 5 times daily (`15 2,7,11,16,21 * * *`). Configures a SOCKS5 proxy via Cloudflare WARP and runs a Node.js-based Playwright TypeScript agent (`npm start` inside `bot/`).
3. **`kronos_cloud.yml`**: Runs every 6 hours (`0 */6 * * *`). It runs all Python-based scrapers concurrently:
   ```bash
   python scripts/run_all_scrapers.py
   ```
   Followed by other marketing/lead generation engines (`freelance_swarm.py`, `seo_matrix_generator.py`, etc.), calls `/api/sync` on the Cloudflare Worker router, and pushes commits/databases back to Git.
4. **`job-hunt.yml`**: Runs daily at 8:00 AM UTC. It executes:
   ```bash
   python run_once.py
   ```
   *Note: `run_once.py` is referenced but does not exist anywhere in the repository.*
5. **`keepalive.yml`** & **`hydra_immortality_action.yml`**: Run every 12 and 14 minutes, respectively, to ping the Render server `/health` or `/healthz` endpoints and run `core/neon_warmer.py` to keep the DB connection alive.
6. **`pa-autorenew.yml`**, **`pa_auto_renew.yml`**, **`pa_watchdog.yml`**: Renew the PythonAnywhere account via selenium-based automation (`.github/pa_autorenew.py`).

### B. Existing Runner Scripts and CLI Commands
1. **Scraper Runner (`scripts/run_all_scrapers.py`)**:
   Concurrently runs `core/matrix_scrape_handler.py` for all 16 platform sources (LinkedIn, Indeed, Glassdoor, etc.) across pages `[0, 1, 2]` using a `ThreadPoolExecutor` (max 8 concurrent workers) and uploads findings to Cloudflare Worker D1 and PythonAnywhere.
2. **Matrix Scraper CLI (`core/matrix_scrape_handler.py`)**:
   Can be run directly via CLI to scrape a specific platform and page:
   ```bash
   python core/matrix_scrape_handler.py --platform linkedin --page 0
   ```
3. **Background Queue Worker (`core/queue_worker.py`)**:
   Maintains a `while True` polling loop looking for tasks in SQLite `job_queue` using `dequeue_task()`. It supports tasks of type `run_campaign` (fork isolation or inline execution), `cron_tick` (checks for pending campaigns and runs them, executes drip email checks, runs ghost hunter hourly), and `growth_*`.
4. **FastAPI Web Worker Tick (`web/app.py` / `web/app_v2.py`)**:
   - `web/app.py` exposes `@app.post("/api/v2/worker/tick")` which pulls 1-2 tasks from the queue and runs them in a separate process/thread.
   - `web/app_v2.py` exposes `@app.get("/api/cron/tick")` / `@app.post("/api/cron/tick")` which checks for pending campaigns, resets stuck campaigns, and attempts to spawn `run_campaign_cli.py` in the background:
     ```python
     script_path = str(BASE_DIR.parent / "run_campaign_cli.py")
     p = subprocess.Popen(
         [_get_python_executable(), script_path, cid],
         ...
     )
     ```
     *Note: `run_campaign_cli.py` is referenced here but does not exist in the codebase.*
5. **Lightning Runner (`core/lightning_runner.py`)**:
   Contains `run_campaign_lightning(campaign_id, company_limit)` which runs campaigns fast using pre-seeded local database records instead of scraping on-the-fly.

---

## 2. Logic Chain

1. **Scraping and Applying Integration**:
   - Scraping is done either via the `kronos_cloud.yml` pipeline (`scripts/run_all_scrapers.py` uploading to the cloud D1 feed) or directly inside campaigns via `core/campaign_runner.py` using `PAJobScraper` (linked to `JSearch` and `LinkedIn XHR`).
   - Applying (cover letter generation and email sending) is driven by the campaign runner (`run_campaign` inside `core/campaign_runner.py`).
   - Thus, executing the "scraping and applying loop" requires triggering either:
     - The background queue handler processing a `run_campaign` task or a `cron_tick` task.
     - Or executing `run_campaign(campaign_id)` directly for campaigns.

2. **Cron Scheduling (30-Minute Cycle)**:
   - There are two deployment scenarios:
     - **API-Triggered (Strategy A)**: If the project runs as a web server on PythonAnywhere or Render, we can trigger the `/api/v2/worker/tick` or `/api/cron/tick` endpoint. Since `smart-tick.yml` already runs every 5 minutes, running a 30-minute interval trigger is trivial using `curl`.
     - **Serverless/CLI-Driven (Strategy B)**: If we want the GHA runner to execute the process completely serverless (without depending on a running web server), we can create a CLI tick script that boots up, processes the queue once, and exits.

3. **Codebase Gaps**:
   - `web/app_v2.py` attempts to run `run_campaign_cli.py`, which is missing. Creating this script is necessary to support background campaign execution via the cron endpoint.
   - `job-hunt.yml` tries to run `run_once.py`, which is missing. Providing this script will prevent workflow failures in `job-hunt.yml`.

---

## 3. Caveats

- **API Rate Limits**: Running Playwright scraping on GHA runners frequently (every 30 minutes) can hit Google/LinkedIn rate limits and Cloudflare challenge blocks unless routed through a proxy (e.g., SOCKS5 WARP proxy, as implemented in `auto_apply.yml`).
- **Execution Timeout**: If campaigns have large numbers of targets, generating AI cover letters might exceed the GHA runner step timeout (typically 6 hours, which is plenty, but DB connections might time out). Timeout management is handled by the worker's processing limits.

---

## 4. Conclusion

Milestone 2 can be implemented using one of two strategies, along with fixing existing missing CLI scripts.

### Recommendation 1: Create Missing CLI Scripts

1. **`run_campaign_cli.py`** (Resolves background campaign launching in `web/app_v2.py`):
   ```python
   # run_campaign_cli.py (Save at project root)
   import sys
   import asyncio
   import config
   from core.campaign_runner import run_campaign
   from web.app import get_db

   async def main():
       if len(sys.argv) < 2:
           print("Usage: python run_campaign_cli.py <campaign_id>")
           sys.exit(1)
       campaign_id = sys.argv[1]
       await run_campaign(campaign_id, get_db, config)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. **`run_once.py`** (Resolves `job-hunt.yml` workflow):
   ```python
   # run_once.py (Save at project root)
   import asyncio
   import logging
   import config
   from core.job_queue import enqueue_task
   from core.queue_worker import _process_cron_tick_task

   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger("run-once")

   async def main():
       logger.info("Starting single cycle worker tick...")
       # Enqueue a cron tick task to process pending campaigns and sync engine
       enqueue_task("cron_tick", {})
       # We could also process the queue here once
       from core.job_queue import dequeue_task
       task = dequeue_task()
       if task and task["task_type"] == "cron_tick":
           await _process_cron_tick_task(task["id"])
           logger.info("Cycle worker tick complete.")
       else:
           logger.info("No cron_tick task dequeued or queue empty.")

   if __name__ == "__main__":
       asyncio.run(main())
   ```

### Recommendation 2: GHA Workflow Configurations

#### Strategy A: Serverless Queue Processing (CLI/Db-Driven)
This workflow runs every 30 minutes, checks out the repo, sets up Python, installs dependencies, and processes the SQLite `job_queue` once.

Create `.github/workflows/scheduled_jobhunt_loop.yml`:
```yaml
name: Scheduled JobHunt Loop (Serverless)

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

concurrency:
  group: "jobhunt-loop"
  cancel-in-progress: true

jobs:
  run-worker:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt --quiet

      - name: Run Single Cycle Loop
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python run_once.py
```

#### Strategy B: Web-Triggered Worker Tick (API-Driven)
This workflow triggers PythonAnywhere or Render to process 1-2 tasks from the queue every 30 minutes. Extremely lightweight.

Create `.github/workflows/scheduled_api_tick.yml`:
```yaml
name: Scheduled API Worker Tick

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  tick:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Web Worker Tick
        env:
          PA_URL: ${{ secrets.PA_URL || 'https://jhfguf.pythonanywhere.com' }}
        run: |
          echo "Triggering API worker tick..."
          curl -fail -s -X POST "${PA_URL}/api/v2/worker/tick" \
            -H "Content-Type: application/json" \
            -d '{"source": "gh-actions-cron-30m"}'
```

---

## 5. Verification Method

To verify the implementation:
1. **Local Test CLI Command**:
   Execute the proposed scripts locally to verify they run without syntax/runtime errors:
   ```bash
   # Test run_once.py
   python run_once.py
   
   # Test run_campaign_cli.py with a mock campaign ID
   python run_campaign_cli.py mock_id
   ```
2. **Verify Workflow Syntax**:
   Push the changes to a test branch and check the GHA UI. Run the workflow using the `workflow_dispatch` manual trigger button in GitHub Actions.
3. **Verify DB Status**:
   Inspect the `job_queue` and `campaigns` tables to verify that campaign status changes to `running` and then `completed`/`failed` upon script run.

# Handoff Report: Milestone 2 GitHub Actions Scheduled Runner Cron Investigation

## 1. Observation
During the read-only codebase investigation, the following files and directories were inspected:
- **Workflows (`.github/workflows/`)**:
  - `auto_apply.yml`: Scheduled run at specific hours (`15 2,7,11,16,21 * * *`) that executes a TypeScript-based agent in `bot/` using Playwright, routed through a Cloudflare WARP proxy to hide the runner IP.
  - `job-hunt.yml`: Scheduled run daily at 8 AM UTC (`0 8 * * *`) executing `python run_once.py`. *Note: The file `run_once.py` is absent from the workspace.*
  - `kronos_cloud.yml`: Orchestrates 24/7 cloud automation (runs every 6 hours: `0 */6 * * *`) running scraper scripts concurrently (`scripts/run_all_scrapers.py`), Upwork bidding, lead generation, auto-marketing, and Cloudflare Worker sync.
  - `smart-tick.yml`: Scheduled worker tick that runs every 5 minutes (`*/5 * * * *`) and performs a POST request to `${PA_URL}/api/v2/worker/tick` to process queued tasks.
- **Scheduled Runner Scripts and CLI Commands**:
  - `web/cron_trigger.py` (lines 1-11):
    ```python
    """
    JobHunt Pro - PythonAnywhere Cron Trigger
    =============================================
    Standalone script for PA Scheduled Tasks.

    Called every 30 minutes by PA cron:
        python /home/jhfguf/jobhunt/web/cron_trigger.py

    Runs the full job cycle: Search → Apply → Follow-up
    PLUS daily database backup (once per day at first run after midnight UTC).
    """
    ```
  - `web/cloud_tick_router.py` (lines 31-89):
    Defines a `/cloud-tick` endpoint which spawns `web/cron_trigger.py` in the background as a subprocess:
    ```python
    @router.post("/cloud-tick")
    async def cloud_tick_handler(request: Request):
        ...
        script_path = os.path.join(base_dir, "web", "cron_trigger.py")
        cmd = [
            sys.executable,
            script_path,
            "--company-limit", str(company_limit),
            "--max-campaigns", str(max_campaigns),
            "--skip-backup"
        ]
        ...
        p = subprocess.Popen(cmd, ...)
    ```
  - `web/app_v2.py` (lines 9068-9152):
    Defines the `/api/cron/tick` route which resets stuck/zombie campaigns, picks up pending ones, and spawns `run_campaign_cli.py` (which is also absent from the workspace).
- **Core Automation Logic**:
  - `core/multi_tenant.py`: Implements `MultiTenantRunner` which queries the database for active user campaigns, performs fair scheduling, and calls `run_campaign` (from `core/campaign_runner.py`) for active campaigns.
  - `core/campaign_runner.py`: Implements `run_campaign` executing the job hunting cycle (`_discover_jobs`, `_enrich_jobs_emails`, `_generate_cover_letters_for_jobs`, `_send_campaign_emails`).
  - `core/pg_sqlite_shim.py`: Manages the database connection to the remote Neon PostgreSQL database with an automatic fallback to local SQLite (`jobhunt_saas_v2.db`) if `DATABASE_URL` is unset or if `FORCE_SQLITE=1` is specified.
- **Existing Tests**:
  - Run command `pytest` passed successfully (582 passed, 129 warnings in 89.90 seconds).

---

## 2. Logic Chain
1. **The CLI Trigger**: `web/cron_trigger.py` is the designated CLI script in the codebase designed to run the multi-tenant campaign job cycle (`Search → Apply → Follow-up`) via `MultiTenantRunner.tick()`.
2. **Web Trigger Constraints**: While `/cloud-tick` and `/api/v2/worker/tick` endpoints exist, executing persistent subprocesses (like long-running scraper/applicator cycles) from web app request threads on PythonAnywhere faces strict worker timeouts (60 seconds) and webapp recycling rules.
3. **Robust GHA Approach**: Running `web/cron_trigger.py` as a direct CLI command inside a GitHub Actions workflow is the most robust way to run the loop. The Actions virtual machine has a generous timeout (up to 360 minutes), meaning we avoid web-request truncation or worker-reload crashes.
4. **Environment Secrets**: To run correctly, the script requires a connection to the remote Neon PostgreSQL database and LLM API keys for cover letter generation. Therefore, the GHA workflow must be supplied with the following secrets:
   - `DATABASE_URL` (The Neon PG connection string)
   - `GEMINI_API_KEY` (For Gemini AI models)
   - `GROQ_API_KEY` (For Groq models, if configured)
   - `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (For live reporting notifications)
   Without `DATABASE_URL`, the shim will fallback to a local SQLite database that is created inside the ephemeral GHA runner and discarded immediately after the run ends, failing to persist job applications or campaign progress.

---

## 3. Caveats
- **IP Blocking Risk**: Scraping directly from GitHub runner IPs can trigger CAPTCHAs or Cloudflare blocks on job boards. However, `core/matrix_scrape_handler.py` monkey-patches scrapers to route queries through a Cloudflare Worker Google Cache scraper (`WORKER_URL = "https://jobhunt-pro-router.samsalameh-cv.workers.dev"`), which mitigates this. If IP blocking is still encountered during applications, the workflow setup should be updated to install and configure the Cloudflare WARP proxy, mirroring `.github/workflows/auto_apply.yml`.
- **GHA Minute Consumption**: A standard run takes ~2 minutes. Running it every 30 minutes generates 48 runs per day (~1,440 runs per month, using ~2,880 build minutes).
  - If the repository is *public*, GHA minutes are free and unlimited.
  - If the repository is *private*, this will exceed the 2,000 free minutes limit. In this case, the user should host the cron schedule directly on PythonAnywhere's "Scheduled Tasks" console to execute `python web/cron_trigger.py` locally, or utilize an external cron service (like cron-job.org) to ping the `/api/v2/worker/tick` or `/api/cron/tick` endpoints.

---

## 4. Conclusion & Recommendation
We recommend configuring a new lightweight GitHub Actions workflow (`.github/workflows/scheduled_runner.yml`) that runs every 30 minutes.

### Proposed Workflow Configuration:
```yaml
name: JobHunt Pro - Scheduled Campaign Runner

on:
  schedule:
    # Run every 30 minutes
    - cron: '*/30 * * * *'
  workflow_dispatch: # Allow manual triggers

concurrency:
  group: "scheduled-campaign-runner"
  cancel-in-progress: true # Prevent database locks from concurrent runs

jobs:
  run-campaigns:
    runs-on: ubuntu-latest
    timeout-minutes: 25

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
          pip install -r requirements.txt

      - name: Run Job Campaign Cycle
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python web/cron_trigger.py --company-limit 15 --max-campaigns 3 --skip-backup
```

---

## 5. Verification Method
1. **Local Dry-Run Check**:
   Run the trigger script locally with a dry-run flag to ensure there are no compilation errors or missing local file dependencies:
   ```bash
   DRY_RUN=true python web/cron_trigger.py --skip-backup
   ```
   Inspect `logs/cron_trigger.log` and verify the output.
2. **Pre-Deployment Unit Testing**:
   Ensure all existing system tests pass:
   ```bash
   pytest tests/test_multi_tenant.py
   ```
3. **Manual Trigger**:
   After pushing the workflow to GitHub, trigger it manually via the `workflow_dispatch` button in the GitHub Actions tab, and inspect the logs to verify it runs successfully.

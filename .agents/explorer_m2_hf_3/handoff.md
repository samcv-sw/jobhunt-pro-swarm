# Handoff Report: Milestone 2 — GitHub Actions Scheduled Runner Cron

## 1. Observation

### Existing GitHub Workflows
Under the directory `.github/workflows/`, there are several active workflows performing scheduling and execution tasks:
*   **`auto_apply.yml`** (runs on schedule `15 2,7,11,16,21 * * *`): Runs the TypeScript-based agent in `bot/` folder using Playwright via SOCKS5 proxy:
    ```yaml
    # Lines 51-62
    - name: Run JobHunt Pro Agent (TypeScript)
      working-directory: bot
      env:
        ...
      run: npm start
    ```
*   **`job-hunt.yml`** (runs on schedule `0 8 * * *`): Sets up a Python 3.11 environment, decodes base64 CV, and runs a single cycle via:
    ```yaml
    # Line 34
    - name: Run JobHunt Pro Single Cycle
      run: python run_once.py
    ```
    *Note: The script `run_once.py` is no longer present in the workspace root directory.*
*   **`kronos_cloud.yml`** (runs on schedule `0 */6 * * *`): Runs all python scrapers concurrently via `scripts/run_all_scrapers.py` and runs marketing/SEO engines.
*   **`smart-tick.yml`** (runs on schedule `*/5 * * * *`): Periodically pings the PythonAnywhere webapp worker tick endpoint to process queue tasks:
    ```yaml
    # Lines 33-36
    RESPONSE=$(curl -s --max-time 300 \
      -X POST "${PA_URL}/api/v2/worker/tick" \
      -H "Content-Type: application/json" \
      -d '{"source":"gh-actions-cron"}' || echo '{"processed":0,"errors":["curl_failed"]}')
    ```

### Existing Scheduled Runner Scripts / CLI Commands
*   **`web/cron_trigger.py`**: A standalone CLI command script designed specifically for cron execution.
    *   It contains the CLI parser defining arguments:
        ```python
        # Lines 119-125 in web/cron_trigger.py
        parser = argparse.ArgumentParser(description="PA Cron Trigger")
        parser.add_argument("--company-limit", type=int, default=15)
        parser.add_argument("--max-campaigns", type=int, default=3)
        parser.add_argument("--campaign-id", type=str, default=None)
        parser.add_argument("--skip-backup", action="store_true")
        ```
    *   It executes a full Multi-Tenant campaign runner cycle (Search → Apply → Follow-up) via the `MultiTenantRunner` class in `core/multi_tenant.py`:
        ```python
        # Lines 89-98 in web/cron_trigger.py
        async def run_cycle(company_limit: int = 15, max_campaigns: int = 3, campaign_id: str = None):
            """Run one full job-hunt cycle using MultiTenantRunner."""
            from core.multi_tenant import MultiTenantRunner
            ...
            runner = MultiTenantRunner(company_limit=company_limit, max_campaigns=max_campaigns, campaign_id=campaign_id)
            result = await runner.tick()
        ```
    *   It triggers daily database backups (via `core/auto_backup.py`) once per day after midnight UTC:
        ```python
        # Lines 129-132 in web/cron_trigger.py
        if not args.skip_backup and _should_run_backup():
            logger.info("📦 Daily backup window — running backup before job cycle")
            run_daily_backup()
        ```
*   **`web/cloud_tick_router.py`**: Mounts the `/api/v2/cloud-tick` route in the FastAPI application (`app_v2.py`). When invoked, it uses `subprocess.Popen` to trigger `web/cron_trigger.py` asynchronously in the background.

---

## 2. Logic Chain

1.  **Requirement**: We need to configure a lightweight GitHub Actions workflow (run every 30 minutes) to execute the scraping and applying loop.
2.  **Observation & Existing Infrastructure**: 
    *   The `web/cron_trigger.py` script is already structured as a standalone CLI application.
    *   It handles the entire pipeline: database backups, self-ping/keep-alive, and the multi-tenant campaign execution loop (Search, Apply, Follow-ups).
    *   Instead of writing new scripts or trying to spin up persistent background worker queues (like Procrastinate or Celery which consume substantial resources/time and are not suitable for short-lived GHA runner jobs), we can leverage `web/cron_trigger.py` directly.
3.  **Workflow Design**:
    *   We configure a schedule cron `*/30 * * * *` (runs every 30 minutes).
    *   The runner checks out the repository, initializes a Python 3.11 environment, and installs dependencies via `pip install -r requirements.txt`.
    *   The runner executes `python web/cron_trigger.py --company-limit 15 --max-campaigns 3`.
    *   Necessary database environment variables (`DATABASE_URL`, `NEON_URL`) and API keys must be passed to the runner using GitHub Secrets.

---

## 3. Caveats

*   **GitHub Action Run-Time / Resource Consumption**: A 30-minute cron run means 48 runs per day. On private repositories, this would consume significant free Action minutes. If the repository is public, GitHub Action execution time is free.
*   **IP Blocks / Captchas**: Running web scrapers from GitHub Action runner IPs can result in prompt Cloudflare challenges or IP bans by job boards. While `core/matrix_scrape_handler.py` monkey-patches scrapers to route traffic through the Cloudflare Worker Google Cache scrape worker (`WORKER_URL`), any direct connections may fail or trigger blocks.
*   **Database Contention**: Executing the workflow concurrently with other instances might cause sqlite lock contentions if SQLite is used as the backend database. To mitigate this, a centralized Neon/Supabase PostgreSQL database is strongly recommended and used in production.

---

## 4. Conclusion

The recommended implementation is to add a lightweight GitHub Actions workflow named `.github/workflows/scheduled_runner.yml` configured as follows:

```yaml
name: JobHunt Pro — Scheduled Runner Cron

on:
  schedule:
    - cron: '*/30 * * * *'  # Run every 30 minutes
  workflow_dispatch:      # Allow manual execution from UI

concurrency:
  group: "jobhunt-pro-scheduled-runner"
  cancel-in-progress: true

jobs:
  run-cycle:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout Repository
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

      - name: Run Scheduled Loop
        run: |
          python web/cron_trigger.py --company-limit 15 --max-campaigns 3
        env:
          PYTHONUNBUFFERED: 1
          # Database Configurations
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          NEON_URL: ${{ secrets.DATABASE_URL }}
          # API Keys & Secrets
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          BREVO_API_KEY: ${{ secrets.BREVO_API_KEY }}
          BREVO_ACCOUNT_EMAIL: ${{ secrets.BREVO_ACCOUNT_EMAIL }}
          # Active SMTP Provider Credentials
          GMAIL_SMTP_USER_1: ${{ secrets.GMAIL_SMTP_USER_1 }}
          GMAIL_APP_PASSWORD_1: ${{ secrets.GMAIL_APP_PASSWORD_1 }}
          GMAIL_SMTP_USER_2: ${{ secrets.GMAIL_SMTP_USER_2 }}
          GMAIL_APP_PASSWORD_2: ${{ secrets.GMAIL_APP_PASSWORD_2 }}
          # Add extra GMAIL env definitions as needed
```

---

## 5. Verification Method

To verify the setup independently:
1.  **Syntax Verification**: Inspect the yaml structure of the proposed workflow and run a yaml validator or local workflow runner like `act`.
2.  **Dry Run Execution**: Manually execute the CLI script locally using:
    ```bash
    python web/cron_trigger.py --company-limit 5 --max-campaigns 1 --skip-backup
    ```
    This verifies that the CLI script resolves imports, successfully loads database configurations, and processes the multi-tenant runner cycle without error.
3.  **Unit Tests**: Run the existing multi-tenant test suite:
    ```bash
    pytest tests/test_multi_tenant.py -v
    ```

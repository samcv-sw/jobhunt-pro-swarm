# PythonAnywhere Cron Setup Guide

## Goal
Run JobHunt Pro job cycles automatically every 30 minutes on PythonAnywhere free tier.

## Prerequisites
- Already deployed on PythonAnywhere (https://jhfguf.pythonanywhere.com ✅)
- Web app is running via `wsgi_pa.py` -> `web/app_v2.py`

## Setup Steps

### 1. Verify the Cron Trigger Script

The file `web/cron_trigger.py` is already created. It runs the full Orchestrator cycle (Search → Apply → Follow-up).

Test it manually first:

```bash
# SSH into PA or open a Bash console from the PA dashboard
cd ~/jobhunt
python web/cron_trigger.py
```

Expected output:
```
2025-xx-xx xx:xx:xx - PA-CRON - INFO -  PA CRON — Starting Job Cycle
...
2025-xx-xx xx:xx:xx - PA-CRON - INFO -  PA CRON — Cycle Complete
```

### 2. Configure the Cron Task (30 min interval)

1. Log into https://www.pythonanywhere.com
2. Go to **Tasks** tab (in the top navigation bar)
3. Under "Scheduled tasks" section, set:
   - **Time:** `30` (minutes past the hour → runs at :00 and :30)
   - **Command:** `python /home/jhfguf/jobhunt/web/cron_trigger.py`
4. Click **Create**

![PA Tasks screenshot description: Use UTC time. PA free tier supports one scheduled task.]

### 3. Cron URL Endpoint (Alternative: Webhook-based)

If you prefer a webhook approach instead of a standalone script:

An endpoint `/cron/run-cycle` is also available on the web app:

```
https://jhfguf.pythonanywhere.com/cron/run-cycle?key=YOUR_CRON_SECRET
```

**Note:** PA free tier cron cannot call HTTP endpoints directly. Use the **standalone script method** above. The webhook endpoint is available for use with external cron services (e.g., cron-job.org, UptimeRobot) that can make HTTP GET requests.

### 4. Verify It's Working

After creating the cron task:

1. Wait for the next scheduled run (at :00 or :30)
2. Check the cron log:
   - PA Dashboard → **Tasks** tab → scroll to "Task output"
   - You can click on a specific run to see its output
3. Or check the local log file:
   ```bash
   cat ~/jobhunt/logs/cron_trigger.log
   ```
4. Check the marker file with last run timestamp:
   ```bash
   cat ~/jobhunt/logs/cron_last_run.txt
   ```

### 5. Troubleshooting

| Problem | Solution |
|---------|----------|
| Cron task not running | Check PA free tier: only 1 scheduled task allowed. Delete any old tasks first. |
| Import errors in cron | Check that all dependencies are installed: `pip install -r requirements-cloud.txt` |
| Database locked | SQLite can get locked if the web app and cron both access it. This is normal for small loads; retry happens on next cycle. |
| Script timeout | PA free tasks have a 5-minute timeout. The Orchestrator should complete within that. |
| "ModuleNotFoundError" | Ensure PYTHONPATH includes the project root. The script handles this automatically, but verify: `python -c "import sys; print(sys.path)"` |

## How It Works

The cron trigger script `web/cron_trigger.py`:
1. Sets up the Python path to include the project root
2. Creates an `Orchestrator` instance (same as `auto_run.py`)
3. Calls `run_full_cycle()` which:
   - Searches for jobs (curated contacts + live bonus)
   - Applies with AI-tailored cover letters
   - Sends follow-up emails
4. Writes a timestamp marker to `logs/cron_last_run.txt`
5. Returns exit code 0 (success) or 1 (failure)

## Logging

All cron output is logged to two places:
- **PA Dashboard → Tasks:** Shows stdout/stderr of each run
- **Local file:** `~/jobhunt/logs/cron_trigger.log` — persistent, append-only

## Security Note

The `/cron/run-cycle` web endpoint is protected by a `CRON_SECRET` environment variable.
Set it in your PA environment:
```bash
# In PA Bash console:
echo "export CRON_SECRET='your-random-secret-here'" >> ~/.bashrc
```
Or add it to your `.env` file in the project root.

Then access the endpoint as:
```
https://jhfguf.pythonanywhere.com/cron/run-cycle?key=your-random-secret-here
```

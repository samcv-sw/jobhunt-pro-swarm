# JobHunt Pro - Cloud Deployment Guide

Deploy your **entire job application system** to Render.com Free Tier — **$0/month**.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Render.com Free Tier (512MB)             │
│                                                       │
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │  Web Server      │  │  Background Job Cycle     │  │
│  │  FastAPI+Uvicorn │  │  Orchestrator.run_full()  │  │
│  │  Port 8000       │  │  Every 60 min (config)    │  │
│  └────────┬────────┘  └───────────┬──────────────┘  │
│           │                        │                  │
│           └────────┬───────────────┘                  │
│                    │                                   │
│           ┌────────▼────────┐                         │
│           │  SQLite Database │                         │
│           │  jobhunt_saas_v2 │                         │
│           └─────────────────┘                         │
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   ┌──────────┐      ┌──────────────┐
   │  Groq AI  │      │  cron-job.org │
   │  Scoring  │      │  Ping /cron/  │
   │  Letters  │      │  every 30min  │
   └──────────┘      └──────────────┘
```

- **Web Server**: Serves the FastAPI dashboard, API, and health checks
- **Background Cycle**: Runs `Orchestrator.run_full_cycle()` as an async task inside the same process
- **External Cron**: cron-job.org (free) hits `/cron/run-cycle` every 30 min as backup
- **All in one process** — No separate worker needed on free tier

---

## Prerequisites

| Item | Where |
|------|-------|
| GitHub account | https://github.com |
| Render.com account | https://render.com (sign up with GitHub) |
| Groq API key | https://console.groq.com |
| JSearch API key | https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch |
| Telegram bot token (optional) | https://t.me/BotFather |
| cron-job.org account (optional) | https://cron-job.org |

---

## Step 1: Push to GitHub

```bash
cd "C:\Users\samde\Desktop\cv sam new ma3 kimi"

# Initialize git (first time only)
git init
git add .
git commit -m "JobHunt Pro v16.7 - Cloud Edition"

# Create a NEW private repo on GitHub (https://github.com/new)
# Name it: jobhunt-pro
# Keep it PRIVATE

git remote add origin https://github.com/YOUR_USERNAME/jobhunt-pro.git
git push -u origin main
```

> **Security**: The `.gitignore` already excludes `.env`, `*.db`, `logs/`, and other sensitive files. Never commit API keys to git.

---

## Step 2: Deploy to Render.com

1. Go to https://render.com and sign in with GitHub
2. Click **"New"** → **"Blueprint"**
3. Select your `jobhunt-pro` repository
4. Render automatically reads `render.yaml` — click **"Apply"**
5. Wait 2-3 minutes for the first build

Your app will be at: `https://jobhunt-pro.onrender.com`

---

## Step 3: Configure Environment Variables

In Render Dashboard → your app → **Environment** tab, add these **Secret Files**:

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | AI scoring + cover letters | ✅ Yes |
| `JSEARCH_API_KEY` | Job search from RapidAPI | ✅ Yes |
| `GMAIL_SMTP_USER_1` | samatou683@gmail.com | ✅ Yes |
| `GMAIL_APP_PASSWORD_1` | Gmail app password | ✅ Yes |
| `BREVO_API_KEY` | Brevo REST API key for email fallback | Optional |
| `BREVO_ACCOUNT_EMAIL` | Brevo sender email address | Optional |
| `TELEGRAM_BOT_TOKEN` | Telegram notifications | Optional |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Optional |
| `SECRET_KEY` | Session encryption key | ✅ Yes |
| `CANDIDATE_EMAIL` | Your email address | ✅ Yes |
| `CRON_SECRET` | Secret for `/cron/run-cycle` | Optional |

### Override these if needed (defaults are safe):

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | Set to `false` to send real emails |
| `MAX_WORKERS` | `50` | Parallel workers (lower for free tier RAM) |
| `DAILY_SEND_LIMIT` | `200` | Max emails per day |
| `CYCLE_INTERVAL` | `60` | Minutes between background cycles |

> **IMPORTANT**: Start with `DRY_RUN=true` to verify the system works without sending real emails. Change to `DRY_RUN=false` only after everything is verified.

---

## Step 4: Verify Deployment

### Health Check
```bash
curl https://jobhunt-pro.onrender.com/health
# Expected: {"status":"ok"}
```

### Full Health Check
```bash
curl https://jobhunt-pro.onrender.com/health/full
# Shows: services, orders, crypto wallets status
```

### Dashboard
Open `https://jobhunt-pro.onrender.com` in your browser.

### Trigger a Test Cycle
```bash
curl "https://jobhunt-pro.onrender.com/cron/run-cycle?key=YOUR_CRON_SECRET"
# Returns: {"status":"ok","found":0,"applied":0,"followups":0}
```

---

## Step 5: Set Up External Cron (Optional but Recommended)

The system runs background cycles automatically, but if Render spins down after 15 minutes of inactivity, the background task pauses too.

To keep it running 24/7:

1. Go to https://cron-job.org and sign up (free)
2. Create a new cron job:
   - **URL**: `https://jobhunt-pro.onrender.com/cron/run-cycle?key=YOUR_CRON_SECRET`
   - **Schedule**: Every 30 minutes
   - **Method**: GET

This pings your app every 30 minutes, preventing the spin-down AND triggering a job cycle.

---

## Step 6: Monitor via Telegram

Once configured, the system sends Telegram notifications for:
- Campaign start/end
- Applications submitted
- Errors requiring attention

Check your Telegram bot for updates.

---

## Free Tier Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Uptime | 750h/month | ~31 days, more than enough |
| RAM | 512MB | Refresh dashboard less for smaller memory |
| Disk | 3GB persistent | SQLite DB fits easily |
| Idle timeout | 15 min | Wakes on request (~30s delay) |
| Build minutes | 400/month | Only rebuild when you push to GitHub |
| Bandwidth | 100GB/month | More than enough for API calls |

---

## Troubleshooting

### App is not responding
- Render spins down after 15min idle. Wait ~30s for it to wake up.
- Set up cron-job.org to ping every 5 minutes to keep it awake.

### Background cycle not running
- Check logs in Render Dashboard
- Verify background cycle started: look for `"BACKGROUND CYCLE #1"` in logs
- Manually trigger: `curl "https://jobhunt-pro.onrender.com/cron/run-cycle?key=YOUR_CRON_SECRET"`

### Emails not sending
- Check if `DRY_RUN=true` (set to `false` to send)
- Check Gmail credentials in Environment tab
- Check Render logs for SMTP errors
- Check Brevo API key if Gmail fails: verify `BREVO_API_KEY` is set

### Database issues
- SQLite is stored on Render's persistent disk
- If you need to reset: delete `data/jobhunt_saas_v2.db` and restart
- The app will recreate tables automatically on next start

---

## Updating

To update your cloud deployment:

```bash
# Make your changes locally
git add .
git commit -m "Description of changes"
git push
```

Render auto-deploys from GitHub. Wait ~2 minutes.

---

## Cost Breakdown

| Service | Cost | Details |
|---------|------|---------|
| Render.com | $0/mo | Free tier web service |
| GitHub | $0/mo | Private repo, free |
| Groq AI | $0/mo | 14,400 requests/day free |
| JSearch API | $0/mo | 500 requests/month free |
| Gmail SMTP | $0/mo | 100 emails/day per account |
| Brevo API | $0/mo | 300 emails/day fallback |
| Telegram | $0/mo | Free bot API |
| cron-job.org | $0/mo | Free cron scheduling |
| **Total** | **$0/mo** | **Fully free** |

---

## Files Reference

| File | Purpose |
|------|---------|
| [`start_cloud.py`](start_cloud.py) | Cloud entry point — web server + background cycle |
| [`render.yaml`](render.yaml) | Render Blueprint config (auto-read on deploy) |
| [`web/app_v2.py`](web/app_v2.py) | FastAPI web dashboard (served on cloud) |
| [`web/cron_trigger.py`](web/cron_trigger.py) | PythonAnywhere cron script (legacy) |
| [`Dockerfile.cloud`](Dockerfile.cloud) | Docker config for alternative cloud platforms |
| [`Procfile`](Procfile) | Render start command: `web: python start_cloud.py` |
| [`requirements-cloud.txt`](requirements-cloud.txt) | Python dependencies for cloud |
| [`.env.example`](.env.example) | All config vars documented |

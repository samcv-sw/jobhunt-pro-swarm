# JobHunt Pro — Cloud Deployment Guide

Deploy JobHunt Pro for **free** on Railway or Render with SQLite (no PostgreSQL needed).

---

## Quick Comparison

| Feature | Railway Free | Render Free |
|---------|-------------|-------------|
| Credit | $5/month | 750 hours/month |
| RAM | 512MB | 512MB |
| Disk | 1GB | No persistent disk* |
| Custom domain | Yes | Yes |
| Auto-sleep | No | Yes (15min idle) |
| Database | SQLite (included) | SQLite (ephemeral*) |
| Best for | **24/7 operation** | Demo / testing |

> **Recommendation:** Use **Railway** for production — no sleep, persistent disk, and $5 credit covers a small app easily.

> **\*Render free tier** has no persistent disk — SQLite data resets on redeploy. For Render, use the external PostgreSQL add-on ($7/month) or accept ephemeral data.

---

## Option A: Deploy to Railway (Recommended)

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))

### Step 1: Push to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/jobhunt-pro.git
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app) → **New Project**
2. Select **"Deploy from GitHub repo"**
3. Choose your `jobhunt-pro` repository
4. Railway auto-detects the Dockerfile

### Step 3: Configure Environment Variables

In Railway dashboard → your project → **Variables** tab:

| Variable | Value | Required |
|----------|-------|----------|
| `PORT` | *(auto-set by Railway)* | No |
| `DATABASE_URL` | `sqlite:///data/jobhunt_saas_v2.db` | No (default) |
| `DATABASE_URL_SYNC` | `sqlite:///data/jobhunt_saas_v2.db` | No (default) |
| `CANDIDATE_EMAIL` | your_email@gmail.com | Yes |
| `CANDIDATE_PHONE` | +961 70 XXX XXXX | Yes |
| `GEMINI_API_KEY` | your_gemini_key | Recommended |
| `GROQ_API_KEY` | your_groq_key | Recommended |
| `TELEGRAM_BOT_TOKEN` | your_bot_token | Optional |
| `TELEGRAM_CHAT_ID` | your_chat_id | Optional |
| `GMAIL_SMTP_USER_1` | your_gmail | Optional |
| `GMAIL_APP_PASSWORD_1` | your_app_password | Optional |
| `SECRET_KEY` | *(generate random string)* | Yes |
| `MAX_WORKERS` | `50` | No (default) |
| `DAILY_SEND_LIMIT` | `500` | No (default) |
| `DRY_RUN` | `true` | No (default, safety) |
| `CLOUD_MODE` | `true` | No (auto-set) |

### Step 4: Add Persistent Volume (Important!)

Railway free tier includes 1GB disk. To keep your SQLite data:

1. Go to your service → **Volumes** tab
2. Click **"New Volume"**
3. Mount path: `/app/data`
4. Size: 1GB

### Step 5: Deploy

1. Railway auto-deploys on push to `main`
2. Check **Deployments** tab for build logs
3. Once deployed, click the generated URL (e.g., `jobhunt-pro.up.railway.app`)
4. Visit `/health` to verify: should return `{"status": "healthy", ...}`

### Step 6: Custom Domain (Optional)

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"** for a free `.up.railway.app` domain
3. Or add custom domain with your own DNS

---

## Option B: Deploy to Render

### Step 1: Push to GitHub (same as Railway Step 1)

### Step 2: Create Render Service

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Select the `jobhunt-pro` repository

### Step 3: Configure Build Settings

| Setting | Value |
|---------|-------|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements-cloud.txt` |
| Start Command | `python start_cloud.py` |
| Plan | Free |

### Step 4: Configure Environment Variables

Same as Railway (see table above). In Render dashboard → **Environment** tab.

Render's `render.yaml` blueprint is included — it auto-configures most settings when you use **"Blueprint"** deployment.

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render builds and deploys automatically
3. Check logs for any errors
4. Visit the `.onrender.com` URL + `/health`

### ⚠️ Render Free Tier Limitations

- **Spins down after 15 minutes of inactivity** — first request takes ~30s to wake up
- **No persistent disk** — SQLite data is lost on redeploy
- **750 hours/month** — enough for 1 service running 24/7
- For persistent data on Render, add the **PostgreSQL add-on** ($7/month)

---

## Environment Variables Reference

### Required (App Won't Start Without These)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Random string for session encryption |

### Recommended (Core Features)

| Variable | Description |
|----------|-------------|
| `CANDIDATE_EMAIL` | Your email address |
| `CANDIDATE_PHONE` | Your phone number |
| `GEMINI_API_KEY` | Google Gemini API for AI features |
| `GROQ_API_KEY` | Groq API for fast AI inference |

### Optional (Email & Notifications)

| Variable | Description |
|----------|-------------|
| `GMAIL_SMTP_USER_1` | Gmail address for sending |
| `GMAIL_APP_PASSWORD_1` | Gmail app password |
| `BREVO_API_KEY` | Brevo REST API key (email fallback) |
| `BREVO_ACCOUNT_EMAIL` | Brevo sender email address |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications |

### Cloud-Specific (Auto-Configured)

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Auto-set by Railway/Render |
| `DATABASE_URL` | `sqlite:///data/jobhunt_saas_v2.db` | Database connection |
| `CLOUD_MODE` | `true` | Enables cloud optimizations |
| `MAX_WORKERS` | `50` | Reduced for free tier RAM |
| `DRY_RUN` | `true` | Safe default — set `false` to send real emails |

---

## Connecting to a Cloud Database

### Option 1: SQLite (Free, Built-in)

Default for free tier. Data stored in `/app/data/` directory.

- **Railway**: Persistent with volume mount
- **Render**: Ephemeral (data lost on redeploy)

### Option 2: Railway PostgreSQL ($5/month from credit)

1. In Railway dashboard → **New** → **Database** → **PostgreSQL**
2. Railway auto-creates a `DATABASE_URL` variable
3. Your app will auto-detect it (the startup script checks for PostgreSQL URLs)
4. Run `init.sql` to create tables (use Railway's SQL editor)

### Option 3: External PostgreSQL (Neon, Supabase, etc.)

**Neon** (free tier: 0.5GB storage):
1. Sign up at [neon.tech](https://neon.tech)
2. Create a project → copy the connection string
3. Set `DATABASE_URL` and `DATABASE_URL_SYNC` in Railway/Render
4. Add `asyncpg` and `psycopg2-binary` to requirements if using PostgreSQL

**Supabase** (free tier: 500MB storage):
1. Sign up at [supabase.com](https://supabase.com)
2. Create a project → Settings → Database → Connection string
3. Set environment variables as above

---

## Health Check Endpoint

The app exposes `/health` for cloud monitoring:

```bash
curl https://your-app.up.railway.app/health
```

Response:
```json
{
  "status": "healthy",
  "service": "JobHunt Pro",
  "version": "15.0",
  "timestamp": "2026-05-20T17:38:00+00:00",
  "agents": 200,
  "providers": 19,
  "uptime": "ok"
}
```

Both Railway and Render are pre-configured to use this endpoint.

---

## Troubleshooting

### Build Fails
- Check `requirements-cloud.txt` has correct package names
- Ensure `Dockerfile.cloud` exists in repo root
- View build logs in Railway/Render dashboard

### App Crashes on Start
- Check `PORT` environment variable is set (Railway auto-sets it)
- Ensure `/app/data` directory is writable
- Check logs for import errors

### Database Errors
- Verify `DATABASE_URL` is set correctly
- For SQLite: ensure the `data/` directory exists and is writable
- For PostgreSQL: verify connection string and credentials

### Memory Issues (512MB limit)
- Reduce `MAX_WORKERS` to `25` or lower
- Set `DRY_RUN=true` to avoid email sending overhead
- The cloud startup script is optimized for low memory

### Slow First Request (Render)
- Render free tier spins down after 15min idle
- First request takes ~30s to wake up
- Use a cron service (like UptimeRobot) to ping `/health` every 5min to keep it alive

---

## Cost Estimate

| Platform | Monthly Cost | Notes |
|----------|-------------|-------|
| Railway Free | $0 (within $5 credit) | Best for 24/7 |
| Railway + PostgreSQL | ~$1-3/month | From $5 credit |
| Render Free | $0 | Spins down when idle |
| Render + PostgreSQL | $7/month | Persistent data |
| Neon PostgreSQL Free | $0 | 0.5GB, external |

---

## Quick Deploy Checklist

- [ ] Push code to GitHub
- [ ] Create Railway/Render project
- [ ] Set `SECRET_KEY` environment variable
- [ ] Set `CANDIDATE_EMAIL` and `CANDIDATE_PHONE`
- [ ] Set AI API keys (`GEMINI_API_KEY`, `GROQ_API_KEY`)
- [ ] Add persistent volume (Railway only)
- [ ] Deploy and verify `/health` endpoint
- [ ] Set `DRY_RUN=false` when ready to go live
- [ ] (Optional) Configure custom domain
- [ ] (Optional) Set up email provider credentials

# DEPLOY.md — JobHunt Pro Deployment Guide (Zero-Cost, 24/7)
# IMP-125, IMP-129, IMP-130, IMP-132
#
# This guide documents how to deploy the entire platform for $0/month
# using free tiers: Render (backend) + Cloudflare Pages (frontend) +
# Neon PostgreSQL + Upstash Redis

---

# 🚀 JobHunt Pro — Zero-Cost 24/7 Deployment Guide

## Stack Overview

| Service | Purpose | Cost |
|---|---|---|
| **Render** | Backend (FastAPI + Celery + SyncWorker) | $0 Free Tier |
| **Cloudflare Pages** | Frontend (Next.js static export) | $0 Free Tier |
| **Neon PostgreSQL** | Primary database | $0 Free Tier (0.5GB) |
| **Upstash Redis** | Cache + Celery broker | $0 Free Tier (10K cmds/day) |
| **Cloudflare CDN** | Static asset delivery | $0 Free Tier |
| **BetterStack Logtail** | Log drain (replaces Render's 1h logs) | $0 Free Tier (1GB/mo) |

---

## 1. Backend — Render Free Tier

### Prerequisites
- GitHub account with this repo pushed
- Render account at https://render.com

### Steps
1. Go to https://dashboard.render.com → **New → Web Service**
2. Connect your GitHub repository
3. Render auto-detects `render.yaml` — click **Apply**
4. Set environment variables (see table below)
5. Deploy — the service starts automatically

### Required Environment Variables
```
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
GROQ_API_KEY=<from https://console.groq.com>
REDIS_URL=<from Upstash, see section 4>
DATABASE_URL=<from Neon, see section 3>
ENV=production
ALLOWED_ORIGINS=https://your-project.pages.dev,https://your-domain.com
SENTRY_DSN=<optional, from https://sentry.io>
LOGTAIL_SOURCE_TOKEN=<optional, from https://betterstack.com>
TRUSTED_PROXIES=10.0.0.0/8,127.0.0.1
```

### Keep-Alive (Prevents Cold Starts)
Already configured in `render.yaml` — a cron job pings `/healthz` every 14 minutes.
This keeps the free-tier service from sleeping, enabling 24/7 uptime.

---

## 2. Frontend — Cloudflare Pages (IMP-125)

### Prerequisites
- Cloudflare account at https://cloudflare.com
- Frontend code in `frontend/` directory

### Steps
1. Go to https://dash.cloudflare.com → **Pages → Create application**
2. Connect your GitHub repository
3. Set build configuration:
   - **Build command**: `npm run build`
   - **Build output directory**: `out` (for Next.js static export) or `.next`
   - **Root directory**: `frontend`
4. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-render-service.onrender.com
   ```
5. Click **Save and Deploy**

Your site will be live at `https://your-project.pages.dev`

### Custom Domain (Optional)
1. In Cloudflare Pages → **Custom domains → Add domain**
2. Add your domain and Cloudflare handles SSL automatically

---

## 3. Database — Neon PostgreSQL (Free)

1. Create account at https://neon.tech
2. Create a new project → copy the **Connection string**
3. Format: `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
4. Set as `DATABASE_URL` in Render

The Neon warmer cron in `render.yaml` pings the DB every 5 minutes to prevent cold starts.

---

## 4. Cache/Queue — Upstash Redis (Free)

1. Create account at https://upstash.com
2. Create a new Redis database
3. Copy the **REST URL** formatted as Redis URL:
   - Format: `rediss://default:password@endpoint.upstash.io:6379`
4. Set as `REDIS_URL` in Render

**Important**: The app respects the Upstash free-tier 10-connection limit.
`max_connections=10` is already set in `backend/celery_app.py` and `backend/cache.py`.

---

## 5. CDN for Static Assets — Cloudflare (IMP-129)

Cloudflare Pages automatically serves all static assets through Cloudflare's global CDN.
For the backend's `/static/` directory:

1. In Cloudflare Dashboard → **Websites → Add site** (use your Render domain)
2. Set DNS to proxy through Cloudflare (orange cloud icon)
3. Create a **Cache Rule**:
   - URL pattern: `your-app.onrender.com/static/*`
   - Cache level: **Cache Everything**
   - Edge cache TTL: **1 week**

---

## 6. Log Drain — BetterStack Logtail (IMP-130)

Render free tier only keeps logs for 1 hour. To persist logs permanently for free:

1. Create account at https://betterstack.com
2. Go to **Logs → Sources → Create Source**
3. Copy your **Source Token**
4. Set `LOGTAIL_SOURCE_TOKEN=<your-token>` in Render environment variables
5. The app automatically routes Python logging to Logtail when this env var is set

---

## 7. Load Testing (IMP-099)

```bash
# Install Locust
pip install locust

# Run load test (100 concurrent users)
cd tests
locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s \
  --host https://your-app.onrender.com
```

---

## 8. Mutation Testing (IMP-100)

```bash
# Install mutmut
pip install mutmut

# Run mutation tests on ScamDetector
mutmut run \
  --paths-to-mutate core/scam_detector.py \
  --runner "python -m pytest tests/test_scam_detector.py -x -q"

# View results
mutmut results
```

---

## 9. CI/CD Pipeline

All CI is configured in `.github/workflows/ci.yml`:
- ✅ **Push/PR trigger** — runs tests on every push to main
- ✅ **pip-audit** — scans for CVEs in dependencies
- ✅ **Circular import check** — py_compile all files
- ✅ **Ruff lint** — code quality enforcement
- ✅ **Weekly schedule** — Monday 2am UTC

---

## 10. Health Check Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Lightweight Render health check |
| `GET /api/v1/health` | API version health |
| `GET /api/v1/health/detailed` | Full component health (DB, Redis, SMTP, Groq) |

---

## Maintenance Commands

```bash
# Run full test suite
python -m pytest tests/ -q

# Run integrity verifier
python verify_integrity.py

# Check for dead code
python -m vulture . --min-confidence 80 \
  --exclude .venv2,node_modules,archive,__pycache__

# Sort imports
isort . --profile black --skip .venv2 --skip node_modules

# Lint check
ruff check . --select E,F,W --exclude .venv2,node_modules,archive
```

---

*Last updated: 2026-07-12 by Antigravity — IMP-125, IMP-129, IMP-130, IMP-132*

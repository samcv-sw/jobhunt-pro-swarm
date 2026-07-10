# 🚀 JobHunt Pro — Zero-Cost 24/7 Cloud Deployment Guide

Everything you need to run **JobHunt Pro Swarm** permanently on the cloud at **$0/month**.

---

## Architecture Overview

```
                                ┌─────────────────────────┐
   Users (Gulf Region)  ──────► │  Cloudflare Pages (FREE) │  Vue/Next.js frontend
                                │  your-project.pages.dev  │  Unlimited bandwidth
                                └────────────┬────────────┘
                                             │ API calls
                                ┌────────────▼────────────┐
                                │    Koyeb Nano (FREE)     │  FastAPI backend
                                │  your-app.koyeb.app      │  24/7, no sleep
                                └────────────┬────────────┘
                                             │ reads/writes
                          ┌──────────────────┴──────────────────┐
                          │                                       │
               ┌──────────▼──────────┐              ┌────────────▼────────┐
               │   Turso (FREE)       │              │  HF Spaces (FREE)   │
               │  libsql edge DB      │              │  Scrapers + Bot     │
               │  8GB, global replicas│              │  2 vCPU, 16GB RAM   │
               └─────────────────────┘              └─────────────────────┘
```

---

## Step 1 — Database: Turso (FREE, 8GB)

1. Sign up at **https://turso.tech** (GitHub login works)
2. Create a database:
   ```bash
   turso db create jobhunt-pro
   ```
3. Get the URL and auth token:
   ```bash
   turso db show jobhunt-pro --url
   turso db tokens create jobhunt-pro
   ```
4. Note down:
   - `TURSO_DATABASE_URL=libsql://jobhunt-pro-<yourname>.turso.io`
   - `TURSO_AUTH_TOKEN=<token>`

---

## Step 2 — Backend API: Koyeb (FREE, 24/7 always-on)

1. Sign up at **https://koyeb.com**
2. Create a new **Service → Docker** service
3. Connect your GitHub repo OR push the image manually
4. Set the **Dockerfile path** to: `deploy/Dockerfile.koyeb`
5. Add these **Environment Variables** on the Koyeb dashboard:

   | Variable | Value |
   |---|---|
   | `TURSO_DATABASE_URL` | `libsql://your-db.turso.io` |
   | `TURSO_AUTH_TOKEN` | your token |
   | `SECRET_KEY` | any random long string |
   | `OPENAI_API_KEY` | your key (optional) |

6. Set **Port** to `8000`
7. Deploy — your API will be live at `https://your-app.koyeb.app`

> **Why Koyeb?** Unlike Render.com (which sleeps after 15 minutes), Koyeb Nano instances stay alive permanently on the free tier.

---

## Step 3 — Scrapers & Workers: Hugging Face Spaces (FREE, 16GB RAM)

1. Go to **https://huggingface.co/new-space**
2. Choose: **Docker** SDK, give it a name like `jobhunt-scrapers`
3. Push your code or connect GitHub
4. Set the **Dockerfile path** in Space settings to `deploy/Dockerfile.huggingface`
5. Add **Secrets** in Space Settings → Secrets:

   | Secret | Value |
   |---|---|
   | `TURSO_DATABASE_URL` | same as above |
   | `TURSO_AUTH_TOKEN` | same as above |
   | `TELEGRAM_BOT_TOKEN` | your bot token |
   | `OPENAI_API_KEY` | your key |

6. The Space will start both your **Telegram bot** and **Celery scraper workers** automatically via `deploy/hf_entrypoint.sh`

---

## Step 4 — Frontend: Cloudflare Pages (FREE, Unlimited Bandwidth)

1. Go to **https://dash.cloudflare.com** → Pages → Create a project
2. Connect your GitHub repository
3. Set build settings:
   - **Framework preset**: `Next.js (Static HTML Export)`
   - **Build command**: `cd frontend && npm ci && npm run build`
   - **Build output directory**: `frontend/out`
4. Add **Environment Variables**:
   - `NEXT_PUBLIC_API_URL` = `https://your-app.koyeb.app`
   - `NODE_VERSION` = `20`
5. Deploy — your site will be live at `https://your-project.pages.dev`

> You can add a **custom domain** (e.g. `app.yourdomain.com`) for free via Cloudflare DNS.

---

## Environment Variables Summary

Create a `.env` file locally (never commit it):

```env
# Database (Turso — cloud) OR leave empty for local SQLite
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-turso-token

# Backend
SECRET_KEY=your-super-secret-key-here
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=...

# Frontend
NEXT_PUBLIC_API_URL=https://your-app.koyeb.app
```

---

## Monthly Cost: $0

| Service | Free Tier Limit | Always-on? |
|---|---|---|
| Cloudflare Pages | Unlimited bandwidth | ✅ Yes |
| Koyeb Nano | 1 service, 512MB RAM | ✅ Yes (no sleep) |
| Hugging Face Spaces | 2 vCPU, 16GB RAM | ✅ Yes |
| Turso | 8GB, 1B reads/month | ✅ Yes |
| **Total** | | **$0/month** |

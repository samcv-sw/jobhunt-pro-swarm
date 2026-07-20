# Zero-Cost 24/7 Permanent Cloud Hosting Guide

This guide details how to host the entire JobHunt Pro SaaS stack permanently for **$0/month** using free tiers, while completely bypassing idle spin-downs and sleep cycles.

---

## 🏗️ The Zero-Cost Infrastructure Stack

| Component | Platform | Free Tier Specifications | Role in JobHunt Pro |
|-----------|----------|---------------------------|---------------------|
| **Frontend UI** | Vercel | Unlimited bandwidth, custom domains | Next.js Static & Edge rendering |
| **API Backend** | Render | 512MB RAM, 0.1 CPU, auto-spindown | FastAPI FastAPI WSGI wrapper |
| **Database** | Neon | 1 Project, 500MB storage, auto-spindown | Primary PostgreSQL storage |
| **Cache & Queue** | Upstash | 10k requests/day | Redis key-value cache |
| **Routing / Cron**| Cloudflare | 100k requests/day | HTTP Routing & keep-alive crons |

---

## 💤 Bypassing the Sleep Cycle (The Keep-Alive Strategy)

Both **Render Free Tier** and **Neon Free Tier** use aggressive resource conservation settings:
- **Render Web Services**: Automatically spin down to sleep after **15 minutes** of inactivity. The next incoming request experiences a **30 to 60-second cold-start delay**.
- **Neon PostgreSQL DB**: Automatically pauses after **24 hours** of database inactivity. The next database query experiences a **5 to 10-second cold-start delay**.

### The Solution: Cloudflare Workers Cron Trigger
By deploying a Cloudflare Worker on a **Cron Trigger** scheduled to execute every **5 minutes**, we continuously ping our API backend and database endpoints. This guarantees that:
1. Render never detects 15 minutes of inactivity (remaining 100% active).
2. Neon never pauses because queries are executed periodically.
3. End-users experience sub-second response times at all hours.

---

## 🛠️ Step-by-Step Deployment Tutorial

### Step 1: Database Setup on Neon (PostgreSQL)
1. Sign up on [Neon.tech](https://neon.tech) for a free account.
2. Create a new project and select **PostgreSQL 16**.
3. Choose the region nearest to your target users (e.g., Frankfurt/Europe for Gulf audience legibility).
4. Copy the connection string provided:
   `postgresql://[user]:[password]@[host]/neondb?sslmode=require`
5. Configure database connection pools in `config.py` to use a pool size of 3 and dynamic overflow of 2 to avoid exhausting Neon's free tier limits.

### Step 2: Backend Setup on Render (FastAPI)
1. Sign up on [Render.com](https://render.com).
2. Click **New** > **Web Service**.
3. Link your GitHub repository.
4. Set the following configuration parameters:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements_optimized.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Click **Advanced** and add the environment variables:
   - `DATABASE_URL`: Your Neon connection string.
   - `REDIS_URL`: Your Upstash Redis connection string.
   - `JWT_SECRET_KEY`: A cryptographically secure secret string.
6. Click **Deploy**. Note your service URL (e.g., `https://jobhunt-backend.onrender.com`).

### Step 3: Cache Setup on Upstash (Redis)
1. Sign up on [Upstash.com](https://upstash.com).
2. Create a Serverless Redis Database.
3. Restrict database access to **TLS/SSL**.
4. Copy the connection endpoint and password.
5. In your backend configurations, ensure that key requests are cached with an LRU fallback pattern to avoid exceeding the daily limit of 10,000 commands.

### Step 4: Frontend Setup on Vercel (Next.js)
1. Sign up on [Vercel.com](https://vercel.com).
2. Import your Next.js project directory (`frontend/`).
3. Add the env variables:
   - `NEXT_PUBLIC_API_URL`: Your Render backend service URL.
4. Click **Deploy**. Vercel will build and serve your Next.js app on a global edge CDN for free.

### Step 5: Setting Up the Cloudflare Worker Keep-Alive
1. Sign up on [Cloudflare.com](https://cloudflare.com) and go to **Workers & Pages**.
2. Click **Create Application** > **Create Worker**.
3. Name your worker (e.g., `jobhunt-keepalive`).
4. Replace the worker code with the script provided in `cloudflare/keep_alive.js`.
5. Deploy the worker.
6. Go to **Triggers** > **Cron Triggers** > **Add Trigger**.
7. Set the cron expression to `*/5 * * * *` (runs every 5 minutes).

---

## 📈 Monitoring Free Tier Quotas

To ensure your app remains active and costs exactly $0:
- **Upstash Dashboard**: Monitor command metrics. Use local memory cache fallback triggers in code if commands exceed 8,000/day.
- **Render Dashboard**: Check usage logs. The keep-alive worker will consume roughly 43,200 requests/month, well within free bandwidth limits.
- **Neon Dashboard**: Ensure database size stays under 500MB. Set up periodic vacuums to purge deleted candidate data.

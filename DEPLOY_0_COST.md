# JobHunt Pro SaaS - 0 Investment Permanent Architecture

## 1. Frontend (Vue 3) - Hosted on Vercel
**Cost:** $0/forever
**Uptime:** 24/7

**Steps:**
1. Push your `frontend-vue` folder to a GitHub repository.
2. Sign in to [Vercel](https://vercel.com/) with GitHub.
3. Click "Add New Project" and select your repository.
4. Set the Root Directory to `frontend-vue`.
5. Add the Environment Variable: `VITE_API_URL` pointing to your backend URL (e.g. `https://jobhunt-backend.onrender.com`).
6. Click Deploy. Vercel will automatically build and serve your Vue app via CDN.

## 2. Backend (Node.js) - Hosted on Render
**Cost:** $0/forever
**Uptime:** 24/7 (with cron keep-alive)

**Steps:**
1. Push your `backend-node` folder to GitHub.
2. Sign in to [Render](https://render.com/).
3. Create a new "Web Service" connected to your repo.
4. Root Directory: `backend-node`
5. Build Command: `npm install`
6. Start Command: `npm start`
7. Add Environment Variables (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).

**Keeping Render Awake 24/7 for Free:**
Render's free tier spins down after 15 minutes of inactivity. To prevent this:
1. Go to [cron-job.org](https://cron-job.org/) (100% Free).
2. Create an account and add a new cron job.
3. Set the URL to your Render backend health check: `https://your-backend.onrender.com/health`.
4. Set the schedule to run every **10 minutes**.
5. Your Node backend will now run 24/7 indefinitely.

## 3. Database (MySQL2) - Hosted on TiDB Serverless or Aiven
**Cost:** $0/forever

**Steps:**
1. Create a free account on [TiDB Serverless](https://tidbcloud.com/) or [Aiven](https://aiven.io/).
2. Create a free MySQL cluster (TiDB offers 5GB free storage, no credit card required, never sleeps).
3. Copy the connection details provided in their dashboard.
4. Plug those details into your Render Environment Variables for the backend.

You now have a fully operational, highly scalable, and beautiful tech stack running permanently for free!

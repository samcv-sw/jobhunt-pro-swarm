# JobHunt Pro — Cloudflare Deployment Guide
## $0 · 5 min setup · No credit card

---

## Step 1: Create Cloudflare Account
1. Go to https://dash.cloudflare.com/sign-up
2. Enter email + password (no credit card!)
3. Click "Free" plan

## Step 2: Create D1 Database
```
Click "Workers & Pages" (left menu)
→ "D1" (sub-tab)
→ "Create Database"
→ Name: jobhunt-pro-db
→ "Create"
```

Then copy the `database_id` from the page.

Open `cloudflare/wrangler.toml` in a text editor and fill:
```toml
database_id = "PASTE_THE_ID_HERE"
```

## Step 3: Initialize D1 Schema
In the D1 dashboard:
→ Click "jobhunt-pro-db"
→ "Console"
→ Paste contents of `cloudflare/d1_schema.sql`
→ Run

## Step 4: Deploy Worker
**Option A: Online (easier)**
1. Cloudflare Dashboard → "Workers & Pages" → "Create Application"
2. "Create Worker" → Name: `jobhunt-pro-router`
3. Copy/paste the contents of `cloudflare/worker.js`
4. Delete the worker's default content first
5. "Save and Deploy"

**Option B: CLI (if you have npm)**
```bash
cd cloudflare
npm install -g wrangler
wrangler d1 create jobhunt-pro-db    # get the ID
# Edit wrangler.toml → paste database_id
wrangler deploy
```

## Step 5: Bind D1 to Worker
In Cloudflare Dashboard:
1. Click worker name → "Settings" → "Variables"
2. Under "D1 Database Bindings" → "Add binding"
3. Variable name: `DB`
4. D1 Database: `jobhunt-pro-db`
5. "Save"

## Step 6: Deploy Pages (Static Frontend)
1. Cloudflare Dashboard → "Workers & Pages" → "Create Application"
2. "Pages" tab → "Upload assets"
3. Name: `jobhunt-pro`
4. Drag & drop `cloudflare/pages/` folder
5. "Deploy"
6. Go to Settings → "Functions" → "Add route"
7. Route: `/api/*` → Worker: `jobhunt-pro-router`
8. Route: `/_/pa/*` → Worker: `jobhunt-pro-router`

## Done! 🎉
Your site is live at: `https://jobhunt-pro.pages.dev`

Users see a beautiful dashboard. They register, enter Gmail, start applying.
All via Cloudflare → PA backend. $0. 1M users ready.

---

## Testing
- Visit your Pages URL → see the dashboard
- Try registering as a user
- Check "Home" for live stats (via D1)
- Test the worker health: `https://jobhunt-pro-router.your-subdomain.workers.dev/health`

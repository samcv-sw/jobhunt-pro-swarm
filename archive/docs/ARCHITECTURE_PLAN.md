# JobHunt Pro — Comprehensive Architecture & Fix Plan

## Overview

This document outlines the complete architectural plan for:
1. **Cloud Migration** — Move everything to PythonAnywhere (already partially deployed at `jhfguf.pythonanywhere.com`)
2. **Login/Signup Fix** — Cookie-based auth, OAuth, session management
3. **Job Application Fix** — Campaign runner, email engine, pipeline
4. **Full Website Audit** — All 60+ pages checked for quality
5. **General Polish** — Security, performance, UX improvements

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    JobHunt Pro v17                          │
├─────────────────────────────────────────────────────────────┤
│  always_on_loop.py  ←  MultiTenantRunner.tick() loop        │
│  auto_run.py        ←  200-agent swarm orchestrator         │
│  web/app_v2.py      ←  FastAPI (11,820 lines!)              │
│  core/pg_sqlite_shim.py  ←  sqlite3 → Neon PG shim          │
│  core/multi_tenant.py    ←  Multi-tenant campaign runner    │
│  core/email_engine.py    ←  Email sending engine            │
│  core/campaign_runner.py ←  Campaign execution              │
│  config.py          ←  Global sqlite3 hijack + config       │
│  .env               ←  Environment variables                │
└─────────────────────────────────────────────────────────────┘
```

### Database
- **Primary**: Neon PostgreSQL (`postgresql://neondb_owner:***@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb`)
- **Shim**: `pg_sqlite_shim.py` intercepts `sqlite3` imports → converts SQL → PostgreSQL
- **FORCE_PG=1** env var ensures all operations go through Neon PG

### Authentication
- **Cookie-based**: `URLSafeTimedSerializer` from `itsdangerous` signs user_id into cookie
- **30-day expiry**: `max_age=86400*30`
- **Password**: bcrypt hashing with legacy SHA-256 rejection
- **OAuth**: Google + Microsoft OAuth (separate `/auth/*` and `/oauth/*` routes)
- **Rate limiting**: In-memory dict + DB-backed `system_config` table
- **Account lockout**: 5 failed attempts = 30-minute lockout

### Current Deployment
- **PythonAnywhere**: `jhfguf.pythonanywhere.com` (already deployed)
- **Local**: `localhost:8000` via uvicorn
- **Always-on loop**: Running locally as `JobHunt-AlwaysOn` process

---

## PHASE 1: Cloud Migration — Full 24/7 Deployment

### Problem
The always-on loop (`always_on_loop.py`) runs locally on the user's PC. User wants to turn off PC and have everything run 24/7 on cloud.

### Solution: PythonAnywhere + Neon PG + Cloud Cron

#### 1.1 Deploy Web App to PythonAnywhere (Already Done)
- ✅ Web app already at `jhfguf.pythonanywhere.com`
- ✅ Neon PostgreSQL already configured
- ✅ `FORCE_PG=1` already set

#### 1.2 Move Always-On Loop to PythonAnywhere Scheduled Task
- Create `cloud_loop.py` — a lightweight version of `always_on_loop.py` that:
  - Runs `MultiTenantRunner.tick()` once per invocation
  - Is triggered by PythonAnywhere's "Scheduled Task" every 5 minutes
  - Logs to a file that can be viewed via web

#### 1.3 Create Cloud Cron Endpoint
- The `/api/cron/tick` endpoint (already exists at line 11223) should be the cloud trigger
- PythonAnywhere "Always-on task" or scheduled task hits this endpoint
- Add proper authentication via `CRON_SECRET` header

#### 1.4 Database: Neon PG (Already Done)
- ✅ Neon PostgreSQL is the primary database
- ✅ `pg_sqlite_shim.py` handles SQL → PG translation
- ✅ `FORCE_PG=1` forces PG mode

#### 1.5 File Storage
- CV uploads → store in Neon PG as BLOB or use PythonAnywhere's file system
- Logs → store in Neon PG `system_config` table or log to file

---

## PHASE 2: Fix Login/Signup System

### Problems Identified

#### Problem 1: `get_verified_user_id()` uses cookie only — no server-side session
- **File**: [`web/app_v2.py:212`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:212)
- **Issue**: The function reads `user_id` from a signed cookie. If the cookie is stolen via XSS, the attacker has permanent access (30 days).
- **Fix**: Add server-side session validation + IP binding + user-agent fingerprinting

#### Problem 2: `/api/v1/login` uses `request.session` (Starlette session) — inconsistent with cookie auth
- **File**: [`web/app_v2.py:10893`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:10893)
- **Issue**: Sets `request.session["user"]` but the main app uses `get_verified_user_id()` which reads cookie. These are TWO DIFFERENT auth mechanisms.
- **Fix**: Make API login also set the `user_id` cookie, OR make `get_verified_user_id()` check both cookie AND session.

#### Problem 3: OAuth callback creates user with `uuid.uuid4()` but main register uses `user_{uuid.hex[:16]}`
- **File**: [`web/app_v2.py:3418`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:3418) vs [`web/app_v2.py:3219`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:3219)
- **Issue**: Inconsistent user_id format. Google OAuth uses `str(uuid.uuid4())` (e.g., `550e8400-e29b-41d4-a716-446655440000`) while regular register uses `user_{uuid.hex[:16]}` (e.g., `user_a1b2c3d4e5f6g7h8`).
- **Fix**: Standardize to `user_{uuid.hex[:16]}` format.

#### Problem 4: OAuth callback doesn't set `api_key` for new users
- **File**: [`web/app_v2.py:3419-3423`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:3419-3423)
- **Issue**: Google/Microsoft OAuth creates users without `api_key`, which breaks API-based features.
- **Fix**: Add `generate_api_key()` call during OAuth user creation.

#### Problem 5: Login doesn't check if user is active/disabled
- **File**: [`web/app_v2.py:3605`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:3605)
- **Issue**: `SELECT * FROM users WHERE email = ?` — no check for `is_active` or `banned` status.
- **Fix**: Add `AND is_active = 1` or check after fetching.

#### Problem 6: No CSRF protection on login form
- **File**: [`web/templates/login.html:134`](📂 Folders & Projects/cv sam new ma3 kimi/web/templates/login.html:134)
- **Issue**: Login form has no CSRF token. While the app has CSRF middleware, the login form itself doesn't include a token.
- **Fix**: Add CSRF token to login form.

#### Problem 7: Forgot password sends reset link via Telegram (security risk)
- **File**: [`web/app_v2.py:3685-3707`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:3685-3707)
- **Issue**: Reset links are sent via Telegram DM. If Telegram account is compromised, attacker can reset any password.
- **Fix**: Add email verification step before allowing reset. Keep Telegram as notification only.

#### Problem 8: `/force-migrate` endpoint is public
- **File**: [`web/app_v2.py:3446`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:3446)
- **Issue**: Anyone can hit `/force-migrate` to add OAuth columns. Should be admin-only or removed.
- **Fix**: Add admin authentication or remove the endpoint.

#### Problem 9: No logout endpoint that clears server-side session
- **File**: [`web/app_v2.py`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py)
- **Issue**: The sidebar has a logout link but there's no dedicated `/logout` route that clears the session cookie properly.
- **Fix**: Add `/logout` route that clears the cookie.

### Fix Implementation Plan

```python
# Fix 1: Enhanced get_verified_user_id with IP binding
def get_verified_user_id(request: Request) -> str:
    cookie = request.cookies.get("user_id", "")
    if not cookie:
        return None
    try:
        user_id = session_serializer.loads(cookie, max_age=86400 * 30)
        # Optional: verify IP hasn't changed dramatically
        return user_id
    except (BadSignature, SignatureExpired):
        return None

# Fix 2: Standardize user_id format
user_id = f"user_{uuid.uuid4().hex[:16]}"  # Use this everywhere

# Fix 3: Add /logout route
@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("user_id")
    return resp

# Fix 4: Add active check to login
user = conn.execute("SELECT * FROM users WHERE email = ? AND (is_active IS NULL OR is_active = 1)", (email,)).fetchone()
```

---

## PHASE 3: Fix Job Application System

### Problems Identified

#### Problem 1: Campaign runner uses local SQLite for some operations
- **File**: [`core/campaign_runner.py`](📂 Folders & Projects/cv sam new ma3 kimi/core/campaign_runner.py)
- **Issue**: Some campaign operations bypass `pg_sqlite_shim` and use raw `sqlite3.connect()`
- **Fix**: Ensure ALL database operations go through `get_db()` which uses the shim

#### Problem 2: Email engine has hardcoded paths
- **File**: [`core/email_engine.py`](📂 Folders & Projects/cv sam new ma3 kimi/core/email_engine.py)
- **Issue**: References to local file paths for CV attachments
- **Fix**: Store CVs in database or use cloud-accessible paths

#### Problem 3: `/api/jobs/apply/{job_id}` doesn't check authentication
- **File**: [`web/app_v2.py:8550`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:8550)
- **Issue**: Anyone can apply to jobs without being logged in. This is intentional for public job board, but should have rate limiting per email.
- **Fix**: Add rate limiting per applicant email (max 10 applications/hour)

#### Problem 4: Campaign creation doesn't validate user quota
- **File**: [`web/app_v2.py:4178`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:4178)
- **Issue**: Users can create unlimited campaigns regardless of their plan
- **Fix**: Check user's purchased plan/credits before allowing campaign creation

#### Problem 5: No email tracking pixel fallback
- **File**: [`web/app_v2.py:10042`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:10042)
- **Issue**: Email open tracking relies on a tracking pixel. If images are blocked, opens aren't tracked.
- **Fix**: Add link tracking as fallback (redirect through server)

#### Problem 6: Pipeline advancement doesn't validate transitions
- **File**: [`web/app_v2.py:2083`](📂 Folders & Projects/cv sam new ma3 kimi/web/app_v2.py:2083)
- **Issue**: Pipeline can advance from any stage to any stage without validation
- **Fix**: Add state machine validation (discovered → applied → followed_up → interview → offer)

---

## PHASE 4: Full Website Audit

### Pages to Audit (60+ templates)

#### Public Pages (No Auth Required)
| Page | Route | Template | Status |
|------|-------|----------|--------|
| Home | `/` | `index_v4.html` | ✅ Check |
| Pricing | `/pricing` | `pricing_v3.html` | ✅ Check |
| Services | `/services` | `services_v2.html` | ✅ Check |
| Login | `/login` | `login.html` | ⚠️ Needs CSRF |
| Register | `/register` | `register.html` | ⚠️ Needs Turnstile check |
| Forgot Password | `/forgot-password` | `forgot_password.html` | ⚠️ Security concern |
| FAQ | `/faq` | `faq.html` | ✅ Check |
| Blog | `/blog` | `blog.html` | ✅ Check |
| Privacy | `/privacy` | `privacy.html` | ✅ Check |
| Terms | `/terms` | `terms.html` | ✅ Check |
| Trust | `/trust` | `trust.html` | ✅ Check |
| Contact | `/contact` | `contact.html` | ✅ Check |
| Compare | `/compare` | `compare.html` | ✅ Check |
| War Room | `/war-room` | `war_room.html` | ✅ Check |
| API Docs | `/api/docs` | `api_docs.html` | ✅ Check |
| Sitemap | `/sitemap.xml` | — | ✅ Check |
| Robots | `/robots.txt` | — | ✅ Check |

#### Authenticated Pages (Auth Required)
| Page | Route | Template | Status |
|------|-------|----------|--------|
| Dashboard | `/dashboard` | `dashboard_v3.html` | ✅ Check |
| New Campaign | `/new-campaign` | `new_campaign_v2.html` | ✅ Check |
| Campaign Detail | `/campaign/{id}` | `campaign_detail.html` | ✅ Check |
| Sent Emails | `/sent-emails` | `sent_emails.html` | ✅ Check |
| Battle Station | `/battle-station` | `battle_station.html` | ✅ Check |
| Wallet | `/wallet` | `wallet.html` | ✅ Check |
| Stats | `/stats` | `stats.html` | ✅ Check |
| Referral | `/referral` | `referral.html` | ✅ Check |
| Upload CV | `/upload-cv` | `upload_cv_v3.html` | ✅ Check |
| Email Test | `/email-test` | `email_test.html` | ✅ Check |
| Export | `/export` | `export.html` | ✅ Check |
| My Purchases | `/my-purchases` | `my_purchases.html` | ✅ Check |
| Offers | `/offers` | `offers.html` | ✅ Check |
| Admin | `/admin` | `admin.html` | ✅ Check |

#### Common Issues to Check on ALL Pages
1. ✅ Mobile responsiveness
2. ✅ Loading states / spinners
3. ✅ Error handling (try/except blocks)
4. ✅ Empty states ("No campaigns yet")
5. ✅ SEO meta tags (title, description)
6. ✅ Open Graph tags for social sharing
7. ✅ Proper HTTP status codes
8. ✅ XSS prevention (template escaping)
9. ✅ CSRF protection on all forms
10. ✅ Rate limiting on all POST endpoints

---

## PHASE 5: General Polish & Improvements

### Security Improvements
1. **Add Content Security Policy headers** — Already partially done via `SecurityHeadersMiddleware`
2. **Add rate limiting to ALL POST endpoints** — Currently only login/register/forgot/contact
3. **Add API key authentication to all API routes** — Some routes accept `X-API-Key` header, others don't
4. **Remove debug endpoints** — `/debug-db`, `/force-migrate` should be admin-only
5. **Add proper CORS** — Currently only allows PythonAnywhere and localhost

### Performance Improvements
1. **Add database connection pooling** — Currently opens/closes connection per request
2. **Add Redis caching** — For frequently accessed data (pricing, blog posts)
3. **Optimize dashboard queries** — Some queries scan entire tables
4. **Add pagination to all list endpoints** — Campaigns, emails, transactions

### UX Improvements
1. **Add toast notifications** — For async operations (campaign started, email sent)
2. **Add progress bars** — For campaign execution, CV parsing
3. **Add keyboard shortcuts** — For power users
4. **Improve mobile navigation** — Sidebar is desktop-only

### Code Quality
1. **Split `web/app_v2.py` into modules** — 11,820 lines is unmaintainable
   - `web/routes/auth.py` — Login, register, OAuth, forgot/reset password
   - `web/routes/dashboard.py` — Dashboard, stats, pipeline
   - `web/routes/campaigns.py` — Campaign CRUD, execution
   - `web/routes/payments.py` — Wallet, checkout, crypto
   - `web/routes/admin.py` — Admin panel
   - `web/routes/public.py` — Home, pricing, FAQ, blog, etc.
   - `web/middleware.py` — All middleware (Aegis, Iron Cloak, CSRF, etc.)
   - `web/models.py` — Database models and queries

---

## PHASE 6: IMMORTALIZE — Git & Documentation

### Git Setup
```bash
git init
git add .
git commit -m "JobHunt Pro v17 — Full cloud migration + auth fix + app system fix"
git remote add origin <your-repo-url>
git push -u origin main
```

### Documentation
- Update `README.md` with deployment instructions
- Add `CLOUD_DEPLOY.md` with PythonAnywhere setup guide
- Add `API.md` with API documentation

---

## Implementation Order

1. **Phase 1 (Cloud Migration)** — Deploy loop to PythonAnywhere cron
2. **Phase 2 (Login/Signup Fix)** — Fix auth system
3. **Phase 3 (Job Application Fix)** — Fix campaign/email system
4. **Phase 4 (Website Audit)** — Check all pages
5. **Phase 5 (Polish)** — Security, performance, UX
6. **Phase 6 (Immortalize)** — Git commit

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Neon PG connection drops | High | Medium | Add connection retry logic |
| PythonAnywhere restarts app | Medium | High | Use scheduled tasks, not always-on |
| Rate limiting blocks legitimate users | Medium | Low | Add whitelist for admin emails |
| OAuth tokens expire | High | Medium | Add token refresh logic |
| Email sending fails | High | Low | Multiple fallback providers (already implemented) |
| Session cookie stolen | High | Low | Add IP binding + short expiry |

# Backend Core Audit Report

## 1. Executive Summary
This report presents the findings of a comprehensive read-only audit of the JobHunt Pro SaaS backend core files, routers, and configurations. The audit focused on:
- `backend/main.py`
- `backend/routers/*.py`
- `backend/billing.py`
- `backend/database.py`
- `backend/auth.py`
- `backend/limiter.py`
- `core/` (specifically `cover_letter.py`, `job_queue.py`, and `pg_sqlite_shim.py`)
- `config.py`

Several security vulnerabilities (including IDOR, missing webhook auth, and XSS), performance bottlenecks (GC settings and duplicate dependency runs), database portability issues, and multi-tenant SaaS design flaws were identified. A detailed remediation strategy is proposed for each.

---

## 2. Security Vulnerabilities

### Vulnerability 1: Insecure Direct Object Reference (IDOR) on Stripe Checkout Route
* **File**: `backend/billing.py` (lines 19-50)
* **Description**: The `/api/v1/checkout` endpoint accepts a `CheckoutRequest` containing a `user_id` string in the request body. However, the route does not verify that the supplied `user_id` matches the authenticated user's ID encoded in the JWT claims payload returned by `verify_jwt`. This allows any authenticated user to generate checkout sessions and purchase subscription tiers on behalf of any other user.
* **Proposed Fix**: Extract the authenticated user's ID directly from the JWT claims payload (returned by `verify_jwt`) and use it to configure the checkout session, discarding the `user_id` supplied in the request body.
* **Before**:
```python
@router.post("/api/v1/checkout", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def create_checkout_session(request: CheckoutRequest):
    ...
    try:
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            ...
            client_reference_id=request.user_id
        )
        return {"checkout_url": session.url}
```
* **After**:
```python
@router.post("/api/v1/checkout", dependencies=[Depends(rate_limiter)])
async def create_checkout_session(request: CheckoutRequest, payload: dict = Depends(verify_jwt)):
    # Override client_reference_id with verified JWT subject
    verified_user_id = payload.get("sub")
    if not verified_user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")
    ...
    try:
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            ...
            client_reference_id=verified_user_id
        )
        return {"checkout_url": session.url}
```

---

### Vulnerability 2: Missing Webhook Authentication on Bounce Webhooks (Brevo & SendGrid)
* **File**: `backend/routers/webhooks.py` (lines 18-84)
* **Description**: The Brevo and SendGrid bounce webhooks process POST requests and update database user records (`UPDATE users SET email_bounced = 1 WHERE email IN ...`). However, there is no validation to verify that these webhook requests originated from Brevo or SendGrid. An attacker could craft a POST request containing a list of email addresses, and the system would mark those emails as bounced, effectively causing a Denial of Service (DoS) for those users' outreach campaigns.
* **Proposed Fix**: Implement signature or token verification. For SendGrid, verify the `X-Twilio-Email-Event-Webhook-Signature` and `X-Twilio-Email-Event-Webhook-Timestamp` headers using SendGrid's public key. For Brevo, enforce a secure token configured via a URL query parameter or header.
* **Remediation Draft (SendGrid Verification Example)**:
```python
from sendgrid.helpers.eventwebhook import EventWebhook

@router.post("/api/v1/webhooks/sendgrid")
async def sendgrid_bounce_webhook(request: Request) -> dict:
    # Verify SendGrid Webhook Signature
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp")
    body = await request.body()
    
    public_key = os.getenv("SENDGRID_WEBHOOK_PUBLIC_KEY")
    if public_key:
        ew = EventWebhook()
        if not ew.verify_signature(body.decode("utf-8"), signature, timestamp, public_key):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
    ...
```

---

### Vulnerability 3: Public Unprotected Telegram Webhook
* **File**: `backend/routers/telegram.py` (lines 15-29)
* **Description**: The `/webhook/telegram` POST endpoint handles updates sent to the Telegram bot. This route does not perform any authorization check or verify that incoming requests are from Telegram. Attackers who know the path can inject arbitrary mock updates and control the bot's state.
* **Proposed Fix**: Standardize the webhook URL to include a secret token in the path (e.g., `/webhook/telegram/{secret_token}`), or verify the `X-Telegram-Bot-Api-Secret-Token` header sent by Telegram against the bot token.
* **After**:
```python
@router.post("/webhook/telegram/{secret_token}")
async def telegram_webhook(secret_token: str, request: Request) -> dict[str, str]:
    import config
    expected_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if secret_token != expected_token:
        raise HTTPException(status_code=403, detail="Unauthorized webhook source")
    ...
```

---

### Vulnerability 4: HTML Injection / XSS in Email Preview Endpoint
* **File**: `backend/routers/emails.py` (lines 18-48)
* **Description**: The `/api/v1/emails/preview` endpoint directly interpolates raw AI-generated and user-supplied cover letter text (`body`) into a raw HTML template (`html = f"... <p>{body.replace(chr(10), '<br>')}</p> ..."`) without escaping. If a user or the AI injects malicious script blocks or HTML tags, they will render in the admin/dashboard application, leading to HTML Injection or Cross-Site Scripting (XSS).
* **Proposed Fix**: Escape the cover letter body using `html.escape` before building the template.
* **After**:
```python
import html as python_html

# Inside email_preview:
escaped_body = python_html.escape(body).replace("\n", "<br>")
html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>
body{{font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px}}
</style></head>
<body>
<p>{escaped_body}</p>
...
"""
```

---

### Vulnerability 5: Default/Hardcoded Secrets and Addresses in Configuration
* **Files**: `config.py` (lines 17-37, 296-299), `backend/routers/unsubscribe.py` (line 27), `backend/auth.py` (line 24)
* **Description**:
  1. Default fallbacks exist for `JWT_SECRET_KEY` (`"jobhunt-pro-secret-key-32bytes-ok!!"`) if the environment variable is missing. This exposes production deployments to session forging if configured incorrectly.
  2. Hardcoded fallback addresses for BTC, ETH, USDT, and LTC wallets are defined in `config.py`.
  3. Default database URL pointing to local postgres credentials: `"postgresql+asyncpg://jobhunt:jobhunt_password@localhost:5432/jobhunt_db"`.
* **Proposed Fix**: Raise a strict `ValueError` on startup if critical secrets (`JWT_SECRET_KEY`, `DATABASE_URL`) are not defined and `ENV` is set to `"production"`. Do not expose hardcoded fallback crypto wallets.

---

## 3. Performance Bottlenecks

### Bottleneck 1: Overly Aggressive Garbage Collection
* **File**: `backend/main.py` (line 6)
* **Description**: The garbage collection thresholds are set via `gc.set_threshold(50, 5, 5)`. The Python standard default is `(700, 10, 10)`. Setting thresholds this low forces the garbage collector to run continuously on every minor heap allocation, severely degrading API throughput and causing unnecessary CPU spikes.
* **Proposed Fix**: Remove the `gc.set_threshold` override and let Python manage heap collection using standard defaults, or increase to a profile-tuned scale.

---

### Bottleneck 2: Duplicate JWT Validation Dependency Execution
* **File**: `backend/routers/referral.py` (line 21)
* **Description**: The `track_referral` route is defined as:
```python
@router.post("/api/v1/referral/track", dependencies=[Depends(verify_jwt)])
async def track_referral(req: ReferralRequest, payload: dict = Depends(verify_jwt)) -> dict:
```
This causes `verify_jwt` to run twice per request: once as a router dependency, and once to populate the `payload` parameter. This duplicates the JWT decoding, database checks, and rate limit lookups.
* **Proposed Fix**: Remove the decorator-level dependency.
* **After**:
```python
@router.post("/api/v1/referral/track")
async def track_referral(req: ReferralRequest, payload: dict = Depends(verify_jwt)) -> dict:
```

---

### Bottleneck 3: Dual Database Connection Pools Exceeding Cloud Limits
* **Files**: `backend/database.py` and `core/pg_sqlite_shim.py`
* **Description**: The application establishes two independent database connection pools to the same PostgreSQL (Neon) instance:
  1. An asynchronous SQLAlchemy connection pool (`backend/database.py`, `pool_size=3`, `max_overflow=2`, total max = 5 connections).
  2. A synchronous `ThreadedConnectionPool` inside the custom DB shim (`core/pg_sqlite_shim.py`, `max_conn=3` connections).
  Because the free tier of Neon allows a maximum of 10 concurrent connections, a single uvicorn worker process can use up to 8 connections. Under multiple worker processes or Celery concurrency, the server will quickly exhaust database connections, throwing `OperationalError: connection limit exceeded`.
* **Proposed Fix**: Consolidate database connections. Refactor background tasks and scraper metrics to run queries using the primary SQLAlchemy `async_session` rather than relying on a separate synchronous connection pool in the shim.

---

### Bottleneck 4: In-Memory Lockout Contention and Non-Distribution
* **File**: `backend/auth.py`
* **Description**: Lockout tracking uses an in-memory dictionary `_rate_state` guarded by a global threading lock (`_rate_lock`). Under high concurrent login/request volume, the lock will cause thread contention. Furthermore, because it is stored in-memory, the lockout state is not shared across multi-worker server setups, allowing attackers to bypass lockouts by hitting different server processes.
* **Proposed Fix**: Store lockout status in Redis (using simple keys with TTLs like `lockout:ip_address`), leveraging the pre-configured Redis connection.

---

## 4. Design Flaws & Compatibility Issues

### Design Flaw 1: SQL Engine Incompatibility on Raw SQL Queries
* **Files**: `backend/routers/analytics.py` (line 120), `backend/routers/scraping.py` (line 127)
* **Description**: The codebase strictly enforces PostgreSQL in production, yet several endpoints execute database-specific raw SQL queries:
  1. In `get_referral_analytics` (analytics.py):
     `SUM(CASE WHEN converted = 1 THEN 1 ELSE 0 END)`
     In PostgreSQL, comparing a boolean column `converted` to integer `1` raises a database exception: `operator does not exist: boolean = integer`.
  2. In `scrapers_health` (scraping.py):
     `WHERE created_at >= datetime('now', '-7 days')`
     This SQL function is SQLite-specific. Under PostgreSQL, it raises a syntax error.
  Because the FastAPI routers execute these raw queries using the SQLAlchemy async session directly (which bypasses the regex SQL translation in `pg_sqlite_shim.py`), these routes will crash in production when connected to PostgreSQL.
* **Proposed Fix**: Replace raw SQL queries with SQLAlchemy ORM expressions or rewrite the queries to use standard SQL:
  - Use boolean expressions: `SUM(CASE WHEN converted THEN 1 ELSE 0 END)` or `SUM(CASE WHEN converted = true THEN 1 ELSE 0 END)`.
  - Bind dates dynamically: Pass the calculated date limit as a query parameter from Python (e.g. using `datetime.now(UTC) - timedelta(days=7)`) instead of using database-specific date functions.

---

### Design Flaw 2: Hardcoded Candidate Experience in Fallback Templates
* **File**: `core/cover_letter.py`
* **Description**: While the application is designed as a multi-tenant SaaS where users can purchase subscriptions, the fallback templates in `CoverLetterWriter` contain highly specific numbers and experiences belonging to a single candidate (Sam Salameh):
  - "securing 2,000+ remote users across 30+ branch offices"
  - "Reduced WAN costs by 45% through SD-WAN deployment across 50+ sites"
  - "Managed $5M+ network infrastructure budget"
  - "Led SOC/NOC team of 12 engineers"
  If the AI service fails or times out, a tenant's generated cover letter will fall back to these templates and falsely claim they have Sam's specific achievements.
* **Proposed Fix**: Generalize templates for SaaS users (e.g. using dynamic stats from the tenant's profile if available, or providing neutral phrasing that does not fabricate specific stats).

---

### Design Flaw 3: Dead Lockout Check Path
* **File**: `backend/auth.py`
* **Description**: A previous remediation removed all calls to `_record_failure(ip)` from `verify_jwt` and WebSocket endpoints to prevent Denial of Service (DoS) attacks on NAT users. However, `_check_lockout(ip)` and its complex lazy pruning loop are still executed on every single JWT verification request. Since no failures are ever recorded, `_check_lockout` will always check an empty state, rendering the lockout check path dead code.
* **Proposed Fix**: If IP-based lockout is discarded, remove the dead tracking code to streamline the auth pipeline. If lockout is required, implement a combination of IP + username tracking or account-based lockouts.

---

### Design Flaw 4: Ultra-Aggressive Celery Queuing Timeout
* **Files**: `backend/routers/cover_letters.py` (line 52) and `backend/routers/scraping.py` (line 86)
* **Description**: Both routers attempt to enqueue tasks to Celery with a timeout of `0.05` seconds (50ms). If Redis or RabbitMQ latency exceeds 50ms (common in cloud deployments), the task submission raises a `TimeoutError` and falls back to return `"accepted"`. While the task is still sent to Celery in the background, this aggressive timeout causes false alarms and inconsistent status reports.
* **Proposed Fix**: Increase the queueing timeout to `0.2` or `0.5` seconds.

---

## 5. TODOs & Placeholders Catalog
1. **Placeholder 1** (`core/captcha_solver.py`, line 204):
   - **Text**: `This is a placeholder for the audio fallback approach. In practice, many sites use simple CAPTCHAs that our OCR can solve.`
   - **Status**: Non-functional. It returns `None` immediately, omitting audio captcha solving capability.
2. **Placeholder 2** (`core/compliance.py`, line 447):
   - **Text**: `return True  # Placeholder for production verification`
   - **Status**: Non-functional. Hardcoded return of `True` for GDPR erasure verification.

---

## 6. Recommendations & Remediation Roadmap
1. **Critical Actions (Security & Crashing Fixes)**:
   - Update `verify_jwt` in the billing route to extract the `user_id` from the token and block IDOR.
   - Refactor the database queries in `backend/routers/analytics.py` and `backend/routers/scraping.py` to use standard SQL boolean comparisons (`converted = true`) and Python-injected datetime bounds to prevent PostgreSQL crashes.
   - Implement event webhook verification for Brevo and SendGrid routes.
   - Escape output text in the email preview handler.
2. **Optimizations (Performance & Limits)**:
   - Restore default garbage collection thresholds by removing the custom `gc.set_threshold(50, 5, 5)` call.
   - Consolidate database pools or reduce `max_overflow` and shim limits to avoid exceeding Neon's 10-connection limit.
   - Remove the duplicate `Depends(verify_jwt)` dependency from `backend/routers/referral.py`.
3. **Design Cleanups**:
   - Evict the dead lockout checking logic or rebuild it using account-level tracking in Redis.
   - Generalize the fallback cover letter templates to support multi-tenant SaaS users instead of a hardcoded personal CV.
   - Increase the Celery task dispatch timeout to 200-500ms to reduce latency-induced timeout errors.

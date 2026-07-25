# Original User Request

## Initial Request — 2026-07-17T09:21:01+03:00

Fully integrate and wire the Telegram Mini App (HTML/CSS/JS) with the FastAPI backend, serving static files at `/telegram-miniapp/` and replacing the external Cloudflare Workers URLs with local FastAPI endpoints.

Working directory: `C:\\Users\\samde\\Desktop\\📂 Folders & Projects\\cv sam new ma3 kimi`
Integrity mode: benchmark

## Requirements

### R1. Static Files Mounting
Configure the FastAPI application in `backend/main.py` to serve the static files in the `telegram_miniapp/` directory under the route `/telegram-miniapp`.

### R2. Backend REST API Endpoints
Create a new router `backend/routers/telegram_app.py` and register it in `backend/main.py` implementing:
- `GET /api/v1/user/{userId}`: Fetch user credits and invites.
- `POST /api/v1/queue/status`: Queue status updates.
- `POST /api/v1/checkout`: Create mock crypto invoice URL checkout.
Update `telegram_miniapp/app.js` to send requests directly to the local origin `/` instead of the hardcoded Cloudflare worker URL.

### R3. Automated Tests & Build Safety
- Implement a test suite `tests/test_telegram_miniapp.py` verifying the mounted static assets and all API endpoints return valid JSON/responses.
- Ensure all 660+ existing backend tests execute and pass at 100%.

## Acceptance Criteria

### Static App Serving
- [ ] Accessing `/telegram-miniapp/index.html` returns the mini app page.
- [ ] Assets `styles.css` and `app.js` load cleanly under `/telegram-miniapp/`.

### API Integration
- [ ] `GET /api/v1/user/{userId}` returns JSON with `credits` and details.
- [ ] `POST /api/v1/queue/status` updates the user status in database.
- [ ] `POST /api/v1/checkout` returns JSON containing a realistic mock `invoice_url`.

### Verification
- [ ] Running `pytest tests/test_telegram_miniapp.py` passes 100%.
- [ ] All 660+ existing backend tests pass.

## Follow-up — 2026-07-22T09:36:46Z

JobHunt Pro: A 100% $0 cloud-native, 24/7 autonomous SaaS empire with an automated dual-channel self-marketing engine (Cold Email + LinkedIn/X/Reddit Social Swarm) that acquires paying clients and scales corporate leads 24/7 without local PC execution.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. 24/7 Zero-PC Autonomous Cloud Architecture
- Operate 24/7 continuously on $0 free-tier cloud infrastructure (Vercel, Render, Cloudflare, GitHub Actions Cron, Supabase/Neon).
- Zero runtime or memory dependencies on local PC.

### R2. Dual-Channel B2B Lead Generation & Automated Outreach Swarm
- Autonomous scraping and enrichment of corporate hiring manager leads.
- Multi-step personalized cold email sequence generator & dispatch tracking.
- Social media viral growth post generator for LinkedIn, X (Twitter), and Reddit.

### R3. Ray Dalio & Paul Graham Elite SaaS Standard
- Real-time lead conversion analytics dashboard in web/templates/.
- High-converting onboarding flow with Gulf RTL/LTR dual support (Cairo/Tajawal typography, dynamic CSS logical properties).

## Acceptance Criteria

### Infrastructure & Cloud Automation
- [ ] 24/7 GitHub Actions & Render keep-alive cron ticks execute cleanly in sub-5s.
- [ ] Database shim auto-detects cloud PostgreSQL with seamless SQLite fallback.

### Marketing & Acquisition
- [ ] B2B Growth Swarm generates verified LinkedIn/X/Reddit social campaigns every cloud tick.
- [ ] Cold email sequence generator formats multi-step personalized sequences for target companies.


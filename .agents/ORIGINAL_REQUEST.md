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

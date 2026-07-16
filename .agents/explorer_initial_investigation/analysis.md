# JobHunt Pro — Initial Investigation Analysis

This report presents findings from an audit of JobHunt Pro's test status, styling, input directions, frontend build, and FastAPI backend security and database configuration.

---

## 1. Pytest Baseline & Test Count
The backend test suite was run using `pytest` inside the root directory.

### Baseline Metrics
- **Total Tests Collected**: 621
- **Total Tests Passed**: 621
- **Pass Rate**: 100%
- **Total Duration**: 113.60 seconds

### Key Test Categories
The test suite consists of E2E, unit, integration, and security checks:
- **End-to-End (`tests/e2e/`)**: Covers core scenarios including database connections, backend APIs, frontend, cover letter generation, dashboard logic, job scrapers, authentication, CI/CD pipelines, and unauthorized request handling.
- **Security & Hardening (`tests/test_...`)**: Includes adversarial security checks, ban shield/rate limiter, anti-ban mechanisms, circuit breakers, CORS origin checks, JWT rotation stress tests, and API contracts.
- **Localized Features**: Validates specific behaviors such as the Arabic ATS matcher, Celery worker integration, multi-tenant databases, custom PgBouncer routing shim, and LLM provider fallback pools.

---

## 2. Physical Styling Properties vs. Logical Properties
The styling implementation was audited for compliance with CSS logical properties (critical for right-to-left (RTL) Arabic layout rendering).

### Findings
- **High Compliance**: The project is heavily refactored to enforce logical properties. Physical properties like `margin-left`, `margin-right`, `padding-left`, and `padding-right` are absent in styles and Tailwind classes.
- **Logical Utility Classes & Inline Styles Used**:
  - `margin-inline-start`, `margin-block-end`, `margin-block-start`, `margin-inline`
  - `padding-block`, `padding-inline`
  - `inline-size` (width), `block-size` (height)
  - `max-inline-size`, `min-block-size`
- **Exceptions (Non-violations)**:
  - `web/templates/translate_batch4.py`: A mapping table/conversion script contains physical properties as keys to convert them to logical properties.
  - Text comments referencing physical layouts (e.g. `Row 2: Left: Historical Table | Right: Analytics Card` in `frontend/src/app/dashboard/page.tsx`).
  - Native browser filters containing substrings matching physical words (e.g. `brightness(1.12)` matching `right` due to the substring `bright` in `frontend/src/app/globals.css`).

---

## 3. Form Input `dir="auto"` Audit
All `<input>`, `<textarea>`, and `<select>` elements in HTML templates (`web/templates/`) and Next.js source code (`frontend/src/`) were scanned.

### Next.js Frontend
All form inputs, textareas, and select elements in `frontend/src/` strictly use `dir="auto"`. No violations were found.

### HTML Templates
Two files contain `<input>` and `<select>` elements that lack `dir="auto"`. These elements are critical for Arabic/RTL input support:
1. **`web/templates/growth_station.html`**:
   - Line 193: `<select id="agent-type" ...>`
   - Line 203: `<input type="text" id="keyword" ...>`
   - Line 208: `<input type="text" id="location" ...>`
   - Line 213: `<select id="max-leads" ...>`
   - Line 296: `<select id="filter-source" ...>`
   - Line 297: `<input type="text" id="search-input" ...>`
   - Line 301: `<input type="checkbox" id="select-all" ...>`
   - Line 494: `<input type="text" id="campaign-name" ...>`
   - Line 521: `<input type="checkbox" class="lead-checkbox" ...>`
2. **`web/templates/en/growth_station.html`**:
   - Line 193: `<select id="agent-type" ...>`
   - Line 203: `<input type="text" id="keyword" ...>`
   - Line 208: `<input type="text" id="location" ...>`
   - Line 213: `<select id="max-leads" ...>`
   - Line 296: `<select id="filter-source" ...>`
   - Line 297: `<input type="text" id="search-input" ...>`
   - Line 301: `<input type="checkbox" id="select-all" ...>`
   - Line 494: `<input type="text" id="campaign-name" ...>`
   - Line 521: `<input type="checkbox" class="lead-checkbox" ...>`

---

## 4. Next.js App Build Status
The Next.js production build was run via `npm run build` inside `frontend/`.

- **Build Outcome**: Successful (exit code 0).
- **TypeScript Check**: Completed successfully in 8.8 seconds.
- **PWA Compilation**: Successfully registered service worker `/sw.js`.
- **Static Page Generation**: Generated all 5 pages successfully.
- **Generated Routes**:
  - `○ /` (Static homepage)
  - `○ /_not-found` (Static 404 page)
  - `○ /dashboard` (Static user dashboard)

---

## 5. FastAPI Backend Linting, DB Leaks, JWT & PgBouncer
We performed static analysis and security auditing on files under `web/routers/` and `web/app_v2.py`.

### Undefined Variables (F821)
- **Status**: Checked using `ruff` with rule `F821` on `web/routers/` and `web/app_v2.py`.
- **Result**: Zero undefined variable errors were detected.

### Database Session / Connection Leaks
- **Connection Closure**: Correctly enforced.
  - In `core/database.py` (`get_db_session`), the session is managed in a `try...finally` block that guarantees `.close()` is called on every HTTP request.
  - In `backend/database.py` (`get_db`), the session is managed using an `async with async_session() as session:` block.
  - In `web/routers/`, connections retrieved via `get_db()` are wrapped in context managers: `with get_db() as conn:`.

### PgBouncer Connection Configuration
PgBouncer integration is implemented correctly:
- **Statement Cache**: Disabled inside `core/database.py` and `backend/database.py` via `prepared_statement_cache_size=0` and `statement_cache_size=0` configurations in the async engine creation. This prevents `prepared statement does not exist` errors in PgBouncer's transaction pooling mode.
- **Port Mapping**: Neon connection strings are passed through `format_neon_connection_string` which rewrites URLs to use Neon's `-pooler` proxy (port 5432) and appends `sslmode=require` and `prepareThreshold=0` (disabling prepared statements).
- **Pool Sizes**: Heavily restricted to avoid Neon free-tier limit exhaustion (pools are limited to 1-3 connections, with minimal overflow of 2).
- **Connection Recycling**: Idle connection recycling is configured at 280 seconds (under Neon's 300s limit), and `pool_pre_ping=True` is enabled in SQLAlchemy and the psycopg2 custom shim (`core/pg_sqlite_shim.py`) to test connection health.

### JWT & Auth Check Coverage Gaps
While JWT security and session validations are present on most endpoints, we identified critical gaps:
1. **Unprotected System & Debug Endpoints (`web/app_v2.py`)**:
   - `/api/jobs/unscored` (GET): Fully public; does not verify authentication.
   - `/api/jobs/score` (POST): Fully public; does not verify authentication.
   - `/api/debug-cookies` (GET): Fully public; returns all request cookies and headers. This is a severe security issue as it exposes active session cookies and tokens.
   - `/api/debug/test-email` (GET): Fully public; triggers email transmission using active SMTP credentials, serving as an abuse/spam vector.
2. **Authentication Bypass in `/api/v1/groq-proxy` (`web/app_v2.py`)**:
   - The route handler manually checks if `user_id = request.session.get("user_id")` or `api_key_header = request.headers.get("X-API-Key")` is present.
   - However, if the `X-API-Key` header is present, it is never validated against the database table. An attacker can pass `X-API-Key: bypass` to make free, rate-limited proxy calls directly to the server's private Groq API keys.

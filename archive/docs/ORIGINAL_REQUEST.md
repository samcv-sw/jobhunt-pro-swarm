# Original User Request

## Initial Request — 2026-07-03T11:21:11+03:00

Maximize the performance, aesthetics, and architectural reliability of the JobHunt Pro SaaS platform, an automated job application system. The optimization will focus on frontend UI/UX, backend asynchronous execution, and database synchronization, while strictly avoiding malicious or unauthorized security circumvention.

Working directory: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`
Integrity mode: development

## Requirements

### R1. Frontend UI/UX Overhaul
Enforce strict CSS Logical Properties across the frontend to support seamless RTL/LTR layouts. Upgrade the aesthetic to a modern, premium "glassmorphism" design with subtle micro-animations.

### R2. Backend Concurrency Optimization
Refactor the Python backend to utilize asynchronous patterns (FastAPI) and ensure the Celery/Redis task queue is optimally configured for high-throughput, non-blocking execution.

### R3. Database Synchronization
Implement and refine the local-first synchronization pattern, ensuring that the local SQLite WAL-mode database reliably syncs state changes to the remote PostgreSQL instance via an outbox pattern.

## Acceptance Criteria

### Frontend
- [ ] No physical directional CSS properties (e.g., `margin-left`) are used in the main stylesheets.
- [ ] The UI renders a cohesive glassmorphism theme with working animations.

### Backend & Database
- [ ] Celery tasks can be queued via the FastAPI endpoints without blocking the main event loop.
- [ ] Database outbox records are successfully processed by the sync worker.

## Follow-up — 2026-07-03T10:28:14Z

JobHunt Pro is a high-performance SaaS platform. The goal is to maximize its capabilities across five core pillars: AI Engine, Frontend UI/UX, Stealth Scraping, Security/Auth, and Deployment CI/CD.

Working directory: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`
Integrity mode: development

## Requirements

### R1. AI Engine Enhancement
Improve the Cover Letter generation logic in `backend/ai_engine.py` to stream responses using Groq LPU and handle advanced prompt context (e.g. tone matching).

### R2. Frontend UI/UX Expansion
Build a new dedicated dashboard view in the Next.js frontend (`frontend/src/app/dashboard/page.tsx`) that displays live statistics, historical scrapes, and user analytics with modern glassmorphism design.

### R3. Scraper Stealth Hardening
Enhance `scrapers/stealth_ingest.py` to utilize advanced bypass mechanisms, rotating residential proxies, and TLS fingerprint spoofing to achieve near 100% success rates against Cloudflare/DataDome.

### R4. Security & Authentication
Implement JWT-based authentication in the FastAPI backend (`backend/main.py` and a new `backend/auth.py`), requiring a Bearer token for all `/api/v1/*` endpoints. 

### R5. Deployment & Testing
Write a comprehensive End-to-End (E2E) testing suite and ensure the GitHub Actions pipeline in `.github/workflows/production.yml` runs these tests on every push.

## Acceptance Criteria

### AI Engine
- [ ] A programmatic test script successfully connects to the generation endpoint and receives a streamed response chunk by chunk.

### Frontend
- [ ] Running `npm run build` inside `frontend/` succeeds without errors.
- [ ] The new `/dashboard` route renders successfully and contains at least 3 distinct statistical metric components.

### Scraping
- [ ] The scraper can successfully fetch and parse `https://bot.sannysoft.com/` without being blocked.

### Security
- [ ] Making a GET/POST request to `/api/v1/scrape` without an `Authorization: Bearer <token>` header returns a `401 Unauthorized` HTTP status code.

### Deployment
- [ ] Running `python -m pytest tests/e2e/` passes all tests with zero failures.

## Follow-up — 2026-07-03T11:37:04Z

# Teamwork Project Prompt — Draft

> Status: **Launched**
> Goal: Maximum improvement of JobHunt Pro codebase → delegate to teamwork_preview

**JobHunt Pro** is a production SaaS job-hunting automation platform deployed on PythonAnywhere. It scrapes global job boards, auto-applies via AI-personalized emails, manages SMTP pools, and presents a premium web dashboard — all at $0 infrastructure cost with 24/7 uptime.

Working directory: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`
Integrity mode: development

---

## Requirements

### R1. Code Quality, Architecture & Bug Hardening
Audit and improve the core Python backend for correctness, reliability, and maintainability. This includes:
- `core/campaign_runner.py` (55KB) — fix edge cases, add graceful error recovery
- `core/email_engine.py` (86KB) — improve retry logic, dead-letter handling
- `core/multi_source_scraper.py` (51KB) — fix scraper fragility and add source health-checks
- `core/pa_job_scraper.py` (48KB) — improve concurrency and quota management
- `core/ai_tailor.py` (40KB) — improve LLM prompt quality and fallback handling
- `core/ats_matcher.py` (34KB) — improve matching accuracy and performance
- `orchestrator.py` (25KB) — fix scheduling reliability and dead-campaign recovery
- `config.py` (26KB) — consolidate settings, remove duplication
Remove any dead code, fix swallowed exceptions, ensure all exceptions are logged.

### R2. Web UI/UX Overhaul (Templates)
Dramatically improve the visual quality and usability of the web templates in `web/templates/`. The app targets job seekers in the MENA region (Arabic + English, RTL support required).
- All pages must use CSS Logical Properties for RTL/LTR compatibility
- Upgrade dashboard (`user-dashboard`) to a premium, modern aesthetic with live stats
- Improve the CV upload flow, job listing views, campaign management UI
- Add missing loading states, empty states, and error feedback to all forms
- Ensure all pages are mobile-responsive
- Arabic typography must use Cairo/Tajawal fonts, minimum 16px, line-height 1.8

### R3. Test Coverage Expansion
The project has a `tests/` directory with partial coverage. Expand the test suite to cover:
- All critical paths in `campaign_runner.py`, `email_engine.py`, `anti_ban.py`, `ats_matcher.py`
- All scraper modules with mocked HTTP responses
- Auth flows and payment webhook handling
- Ensure `pytest` passes fully with `pytest -x tests/`

### R4. Performance & Scalability Improvements
Profile and optimize the highest-impact bottlenecks:
- Database query consolidation across all modules that use SQLite
- Connection pooling for all HTTP clients (httpx, requests)
- Async/await improvements in any blocking code paths
- Reduce startup time of `orchestrator.py`
- Add caching where repeated expensive computations occur (e.g., ATS scoring)

### R5. Security Hardening
Review and fix security issues found in the `SECURITY_AUDIT_REPORT_2026-06-05.md`:
- Sanitize all user inputs before DB writes
- Ensure no secrets are hardcoded in source files (use `.env` only)
- Add rate limiting to all public API endpoints in the web app
- Ensure CSRF protection is applied to all POST forms
- Review and harden the SMTP credential storage

### R6. Codebase Cleanup & Organization
The root directory has 194+ files including hundreds of one-off scripts and backup files. Clean up without breaking anything:
- Move all `_backups/` content that is safe to archive into a dedicated `archive/` folder
- Consolidate the 30+ one-off deploy scripts into a single `scripts/deploy.py` with subcommands
- Remove empty files, zero-byte logs, and duplicate `.py` files with the same content hash
- Update `IMPROVE_ME.md` with a new "Last Improvement" entry documenting what was done

---

## Acceptance Criteria

### Code Quality
- [ ] `python -m pytest tests/ -x` passes with 0 failures
- [ ] `python -m ruff check core/ web/ orchestrator.py config.py` reports 0 errors
- [ ] No `bare except:` or `except Exception: pass` blocks remain in core files
- [ ] All scraper modules have at least one unit test with mocked HTTP

### UI/UX
- [ ] All HTML templates use `dir="auto"` on form inputs
- [ ] No `margin-left`, `padding-right`, `left:`, `right:` CSS properties remain (use logical properties)
- [ ] Dashboard renders correctly on mobile (≤ 768px viewport)
- [ ] Arabic text uses Cairo or Tajawal font at ≥ 16px

### Performance
- [ ] `orchestrator.py` startup completes in < 3 seconds (measured via `time python orchestrator.py --dry-run`)
- [ ] Anti-ban DB check (`can_apply_to_company`) uses ≤ 1 DB round-trip

### Security
- [ ] `grep -r "password\|secret\|api_key" core/ web/ --include="*.py" -l` returns only files that read from env
- [ ] All web form POSTs include CSRF token validation

### Cleanup
- [ ] Root directory `.py` file count reduced by ≥ 30% (from ~194 to ≤ 135 files in root)
- [ ] `IMPROVE_ME.md` updated with new "Last Improvement" section dated 2026-07-03

## Follow-up — 2026-07-03T21:46:35+03:00

JobHunt Pro is a high-performance automated job application SaaS platform. The goal is to deploy a massive autonomous swarm in "Maximum Overdrive" to audit, harden, and optimize every layer of the platform: Frontend UI/UX, Backend Concurrency, Database Sync, Scraper Stealth, and CI/CD pipelines.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Frontend UI/UX & RTL Polish
Audit the Next.js frontend to ensure all layouts strictly adhere to CSS Logical Properties for seamless RTL support. Enhance the glassmorphism design system to feel premium and dynamic without breaking existing functionality.

### R2. Backend Concurrency & Database Sync
Audit the FastAPI and Celery integration to guarantee zero blocking on the main event loop. Harden the database `sync_worker.py` to ensure it gracefully handles PostgreSQL connection drops and reconnects without crashing the container.

### R3. Scraper Stealth Hardening
Upgrade the `stealth_ingest.py` scraper to reliably bypass advanced anti-bot protections and ensure it returns structured, parsed data (lists of dicts) rather than raw HTML.

### R4. Security Hardening
Ensure all API endpoints (especially `/api/v1/*`) are rigorously protected by JWT Bearer authentication, rejecting unauthorized access.

### R5. E2E Test Suite Validation
Ensure the complete End-to-End testing suite (`tests/e2e/`) accurately validates the entire stack so that the GitHub Actions continuous deployment pipeline remains unbroken.

## Acceptance Criteria

### Frontend Quality
- [ ] Running a search for physical directional properties (e.g., `margin-left`, `right`) across `frontend/src/` returns zero matches.
- [ ] The Next.js app builds successfully without terminal errors (`npm run build`).

### Backend Reliability
- [ ] A concurrency test script demonstrates that dispatching Celery tasks does not block the FastAPI event loop for more than 50ms.
- [ ] The `sync_worker.py` contains explicit `try/except` blocks handling `asyncpg.PostgresConnectionError` with a retry mechanism.

### Scraper Integrity
- [ ] `stealth_ingest.py` returns a structured `list[dict]` containing at minimum `title` and `url` keys when called.

### Security
- [ ] A test script attempting to POST to `/api/v1/scrape` without an `Authorization: Bearer <token>` header receives a `401 Unauthorized` response.

### CI/CD Pipeline
- [ ] Running `pytest tests/e2e/` passes all tests with zero failures, proving the system is ready for automated Render deployment.


## Follow-up — 2026-07-03T20:20:47Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Comprehensive optimization of the JobHunt Pro system. This includes a premium UI/UX redesign, backend code refactoring for performance and security, and enhancements to the AI ATS matching and scraping engines.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. UI/UX Redesign
Overhaul the frontend to be highly premium, dynamic, and responsive while maintaining Arabic RTL support. Do not break existing routes.

### R2. Backend Optimization
Refactor the Python backend for performance and security. Fix existing bugs and ensure the system is production-ready.

### R3. AI & Scraper Enhancements
Improve the speed and ATS matching accuracy of the AI modules and stealth scrapers.

## Acceptance Criteria

### Backend & Scrapers
- [ ] All existing and newly written automated tests must pass without errors.
- [ ] The scraping engine successfully completes a run and stores jobs in the database without crashing.

### Frontend
- [ ] The web app launches successfully locally.
- [ ] An independent agent validates that the new UI loads without console errors and meets the premium design bar.

## Follow-up — 2026-07-03T21:42:42Z

JobHunt Pro is a high-performance automated job application SaaS platform. The goal is to deploy a massive autonomous swarm in "Maximum Overdrive" to audit, harden, and optimize every layer of the platform: Frontend UI/UX, Backend Concurrency, Database Sync, Scraper Stealth, and CI/CD pipelines.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Frontend UI/UX & RTL Polish
Audit the Next.js frontend to ensure all layouts strictly adhere to CSS Logical Properties for seamless RTL support. Enhance the glassmorphism design system to feel premium and dynamic without breaking existing functionality.

### R2. Backend Concurrency & Database Sync
Audit the FastAPI and Celery integration to guarantee zero blocking on the main event loop. Harden the database `sync_worker.py` to ensure it gracefully handles PostgreSQL connection drops and reconnects without crashing the container.

### R3. Scraper Stealth Hardening
Upgrade the `stealth_ingest.py` scraper to reliably bypass advanced anti-bot protections and ensure it returns structured, parsed data (lists of dicts) rather than raw HTML.

### R4. Security Hardening
Ensure all API endpoints (especially `/api/v1/*`) are rigorously protected by JWT Bearer authentication, rejecting unauthorized access.

### R5. E2E Test Suite Validation
Ensure the complete End-to-End testing suite (`tests/e2e/`) accurately validates the entire stack so that the GitHub Actions continuous deployment pipeline remains unbroken.

## Acceptance Criteria

### Frontend Quality
- [ ] Running a search for physical directional properties (e.g., `margin-left`, `right`) across `frontend/src/` returns zero matches.
- [ ] The Next.js app builds successfully without terminal errors (`npm run build`).

### Backend Reliability
- [ ] A concurrency test script demonstrates that dispatching Celery tasks does not block the FastAPI event loop for more than 50ms.
- [ ] The `sync_worker.py` contains explicit `try/except` blocks handling `asyncpg.PostgresConnectionError` with a retry mechanism.

### Scraper Integrity
- [ ] `stealth_ingest.py` returns a structured `list[dict]` containing at minimum `title` and `url` keys when called.

### Security
- [ ] A test script attempting to POST to `/api/v1/scrape` without an `Authorization: Bearer <token>` header receives a `401 Unauthorized` response.

### CI/CD Pipeline
- [ ] Running `pytest tests/e2e/` passes all tests with zero failures, proving the system is ready for automated Render deployment.

## Follow-up — 2026-07-05T17:16:52Z

JobHunt Pro is a high-performance automated job application SaaS platform. The goal is to deploy a massive autonomous swarm in "Maximum Overdrive" to audit, harden, and optimize every layer of the platform: Frontend UI/UX, Backend Concurrency, Database Sync, Scraper Stealth, and CI/CD pipelines.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Frontend UI/UX & RTL Polish
Audit the frontend to ensure all layouts strictly adhere to CSS Logical Properties for seamless RTL support. Enhance the glassmorphism design system to feel premium and dynamic.

### R2. Backend Concurrency & Database Sync
Audit the FastAPI and Celery integration to guarantee zero blocking on the main event loop. Harden the database `sync_worker.py` to ensure it gracefully handles PostgreSQL connection drops and reconnects without crashing the container.

### R3. Scraper Stealth Hardening
Upgrade the `stealth_ingest.py` scraper to reliably bypass advanced anti-bot protections and ensure it returns structured, parsed data (lists of dicts) rather than raw HTML.

### R4. Security Hardening
Ensure all API endpoints (especially `/api/v1/*`) are rigorously protected by JWT Bearer authentication, rejecting unauthorized access.

### R5. E2E Test Suite Validation
Ensure the complete End-to-End testing suite (`tests/e2e/`) accurately validates the entire stack so that the GitHub Actions continuous deployment pipeline remains unbroken.

## Acceptance Criteria

### Frontend Quality
- [ ] Running a search for physical directional properties (e.g., `margin-left`, `right`) across frontend templates or stylesheets returns zero matches.
- [ ] The app builds successfully without terminal errors.

### Backend Reliability
- [ ] Celery tasks dispatch without blocking the main event loop.
- [ ] Database workers gracefully handle PostgreSQL connection drops and reconnect without crashing.

### Scraper Integrity
- [ ] Scrapers return structured `list[dict]` containing at minimum `title` and `url` keys when called.

### Security
- [ ] A test script attempting to POST to `/api/v1/scrape` without an `Authorization: Bearer <token>` header receives a `401 Unauthorized` response.

### CI/CD Pipeline
- [ ] Running the test suite passes all tests with zero failures.


## 2026-07-10T07:16:11Z

Run a comprehensive audit and optimization sweep across the entire JobHunt Pro workspace to maximize performance, system reliability, security, RTL layout standards, scraper stealth, and test suite health.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Concurrency, Async Safety & Web Worker Hardening
- Audit all `asyncio` code, event loops, locking mechanisms, and background thread pools (especially in `web/app_v2.py` and campaign runner/scheduler modules).
- Prevent any post-fork deadlocks, race conditions, or unhandled exceptions in background workers.
- Ensure the WSGI entry point lazy-loader (`LazyASGIApp`) functions perfectly without thread starvation under multi-worker WSGI environments.

### R2. Database Performance & Connection Isolation
- Inspect the SQLite/PostgreSQL shim layers (`core/pg_sqlite_shim.py`, `core/async_db.py`) to guarantee optimal connection pool management.
- Optimize high-frequency queries in `smart_scheduler.py` and `anti_ban.py` to prevent lock contention, redundant roundtrips, and database timeouts.
- Ensure proper resource cleanup and session closing across all async/sync routes.

### R3. Scraper Stealth & Anti-Bot Reliability
- Review `core/stealth.py`, `scrapers/stealth_ingest.py`, and Cloudflare worker proxies to verify anti-bot bypass mechanisms.
- Guarantee robust random Googlebot IP generation and asynchronous, non-blocking proxy harvesting.
- Ensure scrapers return clean, structured parsed data and handle CAPTCHAs/challenges gracefully without crashing.

### R4. UI/UX RTL Compliance & Visual Polish
- Audit all website templates in `web/templates/` and dashboard pages to ensure CSS Logical Properties (e.g., `margin-inline-start`, `padding-inline-end`, `inset-inline-start`) are used exclusively instead of physical directional styling.
- Verify RTL text flow compatibility with standard Arabic typography (Cairo/IBM Plex Arabic fonts, line-height 1.6-2.0, zero letter-spacing) and correct layout rendering.

### R5. E2E Test Suite Health & Warning Isolation
- Investigate and resolve the `RuntimeWarning` concerning unawaited mock coroutines in `tests/test_stealth_parser_and_fallbacks.py`.
- Refactor multi-assertion test cases that rely on `reset_mock()` into isolated, single-responsibility test functions to eliminate warnings and potential leaks.
- Ensure 100% of the 366+ tests pass successfully.

## Acceptance Criteria

### Performance & Concurrency
- [ ] ASGI applications and WSGI worker processes boot and reload cleanly without terminal warnings, slow startup timeouts, or deadlocks.
- [ ] No unhandled thread exceptions or leaked event loops are reported during stress tests.

### Database Stability
- [ ] No connection leaks or locked database conditions occur under parallel query loads.
- [ ] All database manager and session pool variables are correctly initialized and released post-request.

### Scraper Integrity
- [ ] Scraper fetches utilizing curl-cffi, nodriver, or camoufox fallbacks operate cleanly, utilizing randomized Googlebot IPs and residential proxies correctly.
- [ ] `pytest tests/test_stealth_parser_and_fallbacks.py` runs with zero warnings and 100% success.

### RTL & Design
- [ ] Zero references to physical styling rules (`margin-left`, `margin-right`, `padding-left`, `padding-right`, `left`, `right`) exist in styling and layout templates.
- [ ] Forms and input fields are equipped with `dir="auto"` and dynamic direction transformations.

### Test Isolation
- [ ] All 366+ E2E and unit tests pass successfully.
- [ ] Warning-free test execution logs.


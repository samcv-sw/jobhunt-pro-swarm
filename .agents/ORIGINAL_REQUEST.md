# Original User Request

## Initial Request — 2026-07-03T09:28:46Z

# Teamwork Project Prompt — Draft

> Status: **Ready for launch — awaiting user approval**
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

## Follow-up — 2026-07-03T13:12:08Z

Expand JobHunt Pro into a globally scalable enterprise platform by implementing Kubernetes deployments, a Vector DB for RAG, a Mobile App, and Stripe Billing.

Working directory: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`
Integrity mode: development

## Requirements

### R1. Kubernetes (K8s) Deployment
Create a Helm chart in `deploy/k8s/` that orchestrates the entire stack (FastAPI, Next.js, Celery Workers, Redis, Postgres, and SQLite OPFS volume claims) into a scalable Kubernetes cluster.

### R2. Vector Database (RAG)
Integrate a local vector database (like Qdrant or Chroma) in the backend to store and retrieve past cover letters and user writing styles. Update `backend/ai_engine.py` to use these embeddings as context for the Groq LPU.

### R3. Mobile App (React Native)
Initialize a React Native (Expo) project in `mobile/` that provides a cross-platform mobile frontend connecting to the existing FastAPI backend dashboard endpoints.

### R4. Payment Gateway (Stripe)
Integrate Stripe API in `backend/billing.py` to handle subscription tiers (Free, Pro, Enterprise) and track usage limits based on the user's account tier.

## Acceptance Criteria

### Kubernetes
- [ ] Running `helm lint deploy/k8s/` succeeds without errors or warnings.

### Vector DB (RAG)
- [ ] A test script can successfully insert a cover letter text, generate its embedding, and retrieve it using a semantic similarity search.

### Mobile App
- [ ] Running `npx expo export` inside the `mobile/` directory successfully builds the static bundle without compilation errors.

### Billing
- [ ] A programmatic test can hit a `/api/v1/checkout` endpoint and receive a valid Stripe Checkout session URL.

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


## Follow-up — 2026-07-05T17:52:10Z

JobHunt Pro is a high-performance automated job application SaaS platform. The goal is to deploy another round of the autonomous swarm in "Maximum Overdrive" to further audit, optimize, and build upon the previous victory, targeting maximum performance, code quality, and security.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Deep Performance & Concurrency Hardening
Optimize resource utilization across the FastAPI endpoints, Celery workers, and async tasks to minimize response latency and resource overhead.

### R2. Frontend UI/UX & Glassmorphism Refinements
Audit frontend styling to ensure absolute logical spacing compliance, smooth transitions, premium glassmorphism effects, and responsiveness on all viewport sizes.

### R3. Advanced Scraper Stealth & Data Parsing
Refine scrapers to ensure resilient spoofing against high-end anti-bot mitigations and perfect structured data extraction.

### R4. Complete Security Verification
Verify authentication headers and rate-limiting controls across all endpoints to ensure zero vulnerabilities.

### R5. Complete Test Suite Integrity
Run the entire testing suite (`tests/`) to ensure all features work perfectly with zero failures.

## Acceptance Criteria

### Performance & Backend
- [ ] Backend endpoints maintain sub-50ms event loop latency under concurrent load simulations.
- [ ] Database workers gracefully handle connection cycling and database recovery loops.

### Frontend Quality
- [ ] The Next.js project builds successfully with 0 errors.
- [ ] Physical CSS rules (like `margin-left`, `right`) remain at 0 occurrences in source templates/stylesheets.

### Scraper & Security
- [ ] Scraper components return formatted structured dictionaries with correct keys.
- [ ] All sensitive endpoints reject unauthorized calls with appropriate error responses (e.g., `401 Unauthorized`).

### Test Coverage
- [ ] The full test suite runs and passes successfully with 0 failures.

## Follow-up — 2026-07-05T20:14:01Z

You are a recovery sentinel taking over from a previous swarm leader that hit resource limits. The JobHunt Pro optimization swarm (Round 2) is in progress.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Context
The Project Orchestrator (ID: `01d1651c-a32d-43b4-8343-725dffe459ee`) was last seen executing Milestone 4 (Security Hardening & Authentication). The following milestones were already completed:
- ✅ Milestone 1: Backend Performance & DB Sync — CLEAN audit
- ✅ Milestone 2: Frontend UI/UX & RTL Polish — CLEAN audit, 224 tests passing
- ✅ Milestone 3: Scraper Stealth & Proxy Hardening — CLEAN audit
- 🔄 Milestone 4: Security Hardening & Authentication — IN PROGRESS
- ⏳ Milestone 5: Full Test Suite Integrity — pending

## Your Role
1. Read `.agents/handoff.md` to understand current state.
2. Send a resume message to the Project Orchestrator (`01d1651c-a32d-43b4-8343-725dffe459ee`) to continue from Milestone 4.
3. Reschedule Cron 1 (Progress Reporting, */8 * * * *) and Cron 2 (Liveness Checking, */10 * * * *).
4. Monitor progress and spawn the Victory Auditor when the orchestrator claims all milestones are complete.
5. Report back with progress updates.

## Acceptance Criteria
- [ ] All sensitive endpoints reject unauthorized calls with 401 Unauthorized.
- [ ] The full test suite runs and passes with 0 failures.
- [ ] Independent Victory Auditor confirms VICTORY CONFIRMED verdict.

## Follow-up — 2026-07-06T06:36:56Z

The server has restarted. Please check the current progress and status of the Project Orchestrator (Round 2), resume from where it left off, and reschedule all monitoring crons.

## Follow-up — 2026-07-06T07:18:50Z

JobHunt Pro is a high-performance automated job application SaaS platform. The goal is to deploy another round of the autonomous swarm in "Maximum Overdrive" to further audit, optimize, and build upon the previous victory, specifically ensuring the production deployment at https://jhfguf.pythonanywhere.com is completely hardened, synced, and operating at maximum efficiency.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Cloud Database Sync & Performance Hardening
Verify and optimize database queries and synchronization between the local SQLite database and the remote Neon PostgreSQL database (`DATABASE_URL`), ensuring zero data loss and minimal synchronization latency.

### R2. Production Security & Session Hardening
Verify that all API and WebSocket endpoints on the production site strictly enforce rate limits and require valid JWT Bearer tokens. Verify that sessions and cookie data stored in the database are encrypted and protected.

### R3. Scraper Stealth & Ingestion Reliability
Ensure the scraper engine is completely stealthy and resilient to bot-detection on the production site, returning correctly structured listings containing `title` and `url` keys.

### R4. Production Build & CSS Logical Properties
Ensure the production Next.js application compiles cleanly and maintains 100% compliance with CSS Logical Properties, utilizing premium glassmorphism styles and Cairo/Tajawal fonts.

### R5. Complete Test Suite Integrity
Run the entire testing suite (`tests/`) to ensure all features work perfectly with zero failures.

## Acceptance Criteria

### Cloud Database & Sync
- [ ] Database sync operations execute successfully with zero lost records during database connection dropping simulations.
- [ ] Neon PostgreSQL queries execute under 50ms average latency.

### Production Security
- [ ] All sensitive endpoints reject unauthorized calls with `401 Unauthorized` responses.
- [ ] Custom rate-limiting sliding-window logic is active and blocks spam requests.

### Scraper & UI
- [ ] Scraper components return formatted structured dictionaries with correct keys.
- [ ] The Next.js project builds successfully with 0 errors.
- [ ] No physical CSS rules remain in source stylesheets.

### Test Coverage
- [ ] The full test suite runs and passes successfully with 0 failures.

## Follow-up — 2026-07-06T07:24:40Z

The server has restarted. Please check the current progress and status of the Project Orchestrator (Round 3), resume the audit and optimization task, and reschedule the crons.

## Follow-up — 2026-07-06T08:10:27Z

The server has restarted. Please check the current progress and status of the Project Orchestrator (Round 3), resume the audit and optimization task, and reschedule the crons.

## Follow-up — 2026-07-06T08:27:17Z

The user has specifically requested that the swarm reads and consolidates all past chat history and previous improvements (including all blueprints, system architecture reports, and improvement logs in the workspace) to ensure every single improvement is fully implemented, verified, and deployed to the production site at https://jhfguf.pythonanywhere.com with zero regressions. Please instruct the Gen6 Project Orchestrator to execute a comprehensive, deep audit of all previous milestones and confirm 100% execution before triggering the Victory Audit.

## Follow-up — 2026-07-06T09:17:59Z

JobHunt Pro is a premium AI-powered job application SaaS platform at https://jhfguf.pythonanywhere.com. This round targets a **deep, page-by-page content and UI quality revolution** — going beyond metadata fixes to ensure every single page has rich, polished, professional content, premium visuals, working interactions, and maximum quality across the entire codebase.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

---

## Requirements

### R1. Deep Per-Page Content Audit & Enhancement
Audit every full-page HTML template in `web/templates/` and `web/templates/en/`. For each page:
- Ensure all sections are **complete and populated** — no empty sections, placeholder text ("Lorem ipsum", "TODO", "Coming soon"), or broken layouts.
- Every page must have compelling, professional Arabic (for `web/templates/*.html`) and English (for `web/templates/en/*.html`) copy.
- Key pages to prioritize: `index_v3.html` (landing), `pricing_v3.html`, `for_employers.html`, `trust.html`, `services_v2.html`, `faq.html`, `contact.html`, `dashboard_v3.html`, `upload_cv_v2.html`, `ats_scorer.html`, `resume_tailor.html`, `wallet.html`, `war_room.html`, `battle_station.html`.

### R2. Premium UI Polish — Glassmorphism & Animations
For every page that lacks premium feel:
- Add animated gradient backgrounds, glassmorphism cards, vibrant accent colors (gold `#f0c040`, teal `#00d4aa`, purple `#8b5cf6`).
- Add scroll-triggered fade-in animations using Intersection Observer (no external JS libraries).
- Add hover glow effects on all buttons and cards.
- Ensure consistent use of `Cairo`/`Tajawal` for Arabic and `Inter`/`Outfit` for English content.
- Add premium loading states and micro-interactions on interactive elements.

### R3. Navigation & User Flow Integrity
- Audit every internal link across all pages — fix any broken `href` pointing to non-existent routes.
- Ensure the navbar on every public page shows the correct active state.
- Verify the dashboard sidebar highlights the correct active menu item on each dashboard page.
- Add `rel="noopener noreferrer"` to all external links.

### R4. Backend Route & Feature Completeness
- Read `web/app_v2.py` and identify any route that renders a template but returns minimal/empty context (missing key variables like `jobs`, `stats`, `user_data`).
- Add sensible default/empty-state values so pages render gracefully even with no data.
- Ensure all form submissions have proper CSRF-safe patterns and feedback messages.
- Fix any Jinja2 template errors (undefined variable references) found in `web/templates/`.

### R5. Performance & SEO Final Polish
- Add `loading="lazy"` to all `<img>` tags across all templates.
- Add `rel="preload"` hints for critical fonts and CSS in shell/base templates.
- Ensure `<html lang="ar" dir="rtl">` on all Arabic pages and `<html lang="en" dir="ltr">` on all English pages.
- Add structured data (JSON-LD) to the landing page, pricing page, and FAQ page.
- Verify `robots.txt` and `sitemap.xml` are properly configured.

### R6. Full Test Suite — Zero Regression
After all changes, run the complete test suite and confirm all 253 tests pass with zero failures.

---

## Acceptance Criteria

### Content Quality
- [ ] Zero placeholder text ("Lorem ipsum", "TODO", "Coming soon", "محتوى قريباً") found across all templates.
- [ ] Every full page (non-partial) has at least 2 meaningful content sections beyond the header.

### UI Premium Quality
- [ ] Every full page uses dark gradient background and glassmorphism card style.
- [ ] All buttons have hover:transform and hover:box-shadow effects defined.

### Navigation Integrity
- [ ] Running `python qa_audit_r4.py` shows 0 CSS physical violations.
- [ ] No internal `href` links point to routes that return 404 (verified by crawling with `qa_spider.py`).

### Backend Stability
- [ ] No Jinja2 `UndefinedError` exceptions in `_pa_server.log` after a fresh page load sequence.
- [ ] All pages return HTTP 200 when loaded by an authenticated test session.

### Performance
- [ ] All `<img>` tags have `loading="lazy"` attribute.
- [ ] `<html>` tag has correct `lang` and `dir` attributes on all pages.

### Test Suite
- [ ] `python -m pytest tests/ -q` reports **253 passed, 0 failed**.

### Victory
- [ ] An independent Victory Auditor agent reviews all criteria and writes a signed **VICTORY CONFIRMED** report to `.agents/VICTORY_ROUND5.md`.

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

## Follow-up — 2026-07-06T10:14:18Z

JobHunt Pro (https://jhfguf.pythonanywhere.com/) needs a complete A-to-Z audit by fetching every page from the live site, identifying ALL issues (broken buttons, missing content, broken links, UI bugs), and fixing every single one until the website is 100% functional and polished.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Current Baseline
- 253/253 tests passing
- 0 CSS physical violations
- 112/136 templates QA-passing
- VERSION = 17.0

## Requirements

### R1. Live Page-by-Page Audit
Fetch every public page from https://jhfguf.pythonanywhere.com/ using HTTP requests and inspect the HTML response for:
- Broken or missing navigation links
- Buttons with no `href`, `onclick`, or `action` (non-functional)
- Empty sections or missing content
- Truncated text (sentences cut mid-word)
- Missing images or broken `src` attributes
- Forms with no `action` or `method` attributes

Pages to audit:
/, /pricing, /login, /register, /faq, /contact, /trust, /blog, /compare, /services, /for-employers, /referral, /privacy, /terms, /en/, /en/pricing, /en/login, /en/register

### R2. Fix ALL Non-Functional Buttons
Every `<button>` and `<a class="btn">` or `<a class="cta">` on every page must have a valid destination or action:
- 'ابدأ مجاناً' / 'Get Started Free' buttons must link to /register
- Pricing plan buttons must link to /checkout or /register
- All social share buttons must have valid URLs
- Form submit buttons must be inside a `<form>` with a valid `action`
- Fix empty href='#' placeholders with real routes

### R3. Fix ALL Content Issues Found on Live Pages
Every page must have:
- Complete, non-truncated text in all sections
- All FAQ questions must have full answers (no empty answer divs)
- Contact page must have a working contact form (name, email, message + submit)
- Pricing page must show all plans clearly with prices and features
- Landing page hero text must be 100% complete
- No lorem ipsum, TODO, or placeholder copy anywhere

### R4. Fix Navigation Consistency
- Every page must include the nav and footer
- Active nav link highlighted correctly on each page
- Mobile hamburger menu working on all pages
- Language switcher present and correct on all pages

### R5. Zero Regression
After all fixes: `python -m pytest tests/ -q` must report 253 passed, 0 failed.

## Acceptance Criteria

### Live Page Audit
- [ ] All 18 public pages return HTTP 200
- [ ] Zero buttons with missing href/onclick/action

### Button Functionality  
- [ ] 'ابدأ مجاناً' on homepage links to /register
- [ ] All pricing plan CTAs link to /checkout or /register
- [ ] Contact form has name, email, message fields and submit button with action

### Content Completeness
- [ ] Zero truncated sentences on any live page
- [ ] FAQ page has at least 8 complete Q&A pairs
- [ ] Pricing page shows plans with prices

### Test Suite
- [ ] `python -m pytest tests/ -q` reports 253 passed, 0 failed

### Victory
- [ ] Independent Victory Auditor writes `.agents/VICTORY_ROUND7.md`

## Follow-up — 2026-07-06T19:52:55Z

Audit, optimize, and refactor the entire JobHunt Pro workspace to achieve 100% engineering quality, architectural elegance, type-safety, secure anti-ban protection, and styling compliance.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Architecture, Code Quality & Modularization
Audit all python modules. Modularize functions exceeding 150 lines of code, improve type safety, and annotate all core functions with parameter and return type hints. Add clean, structured docstrings to undocumented helper files.

### R2. Styling, CSS Logical Properties & Localization Compliance
Audit all styles and HTML templates in `web/templates/` and stylesheets. Ensure absolute compliance with CSS Logical Properties (replace physical values like `margin-left/right` or `padding-left/right` with `margin-inline-start/end` or `padding-inline-start/end`). Ensure proper Arabic fallback typography (`'Cairo', 'IBM Plex Arabic', 'Tajawal'`) and directionality layouts (`dir="auto"`, `--text-x-direction` variables).

### R3. Security & Anti-ban Auditing
Verify and harden Aegis Shield, BanShield v3, rate limiters, and OAuth security. Ensure csrf protection is configured across all public web forms.

### R4. Test Coverage Expansion
Identify uncovered/untested parts of the core engine and write additional unit or integration tests to achieve optimal codebase test coverage.

## Acceptance Criteria

### Execution & Verification
- [ ] No regression: All existing 253/253 unit and E2E tests must pass successfully.
- [ ] Compilation & Linting: All modified python files must compile cleanly with zero errors.
- [ ] Code Modularity: No single refactored function exceeds 150 lines.
- [ ] CSS Logical Properties: Zero occurrences of physical layouts (e.g., `margin-left`, `padding-right`) in modified CSS and HTML templates.
- [ ] Type Safety: Type annotations present on all modified and newly created function definitions.
- [ ] Test coverage: Newly added tests run successfully along with the test suite.


## Follow-up — 2026-07-07T07:57:18Z

Full structural auditing, security scans, and code improvements (safe, non-breaking changes only) on the JobHunt Pro codebase.

Working directory: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`
Integrity mode: benchmark

## Requirements

### R1. Deep Code Audit & Repair
Find and fix hidden logic flaws, unhandled exceptions, race conditions, and typing inconsistencies across all modules.

### R2. High-Performance Optimization
Harden database query patterns, async/blocking code, and event-loop efficiency without impacting core logic.

### R3. Comprehensive Security Audits
Eliminate SQL injection risks, insecure environment defaults, and unauthenticated endpoints.

## Acceptance Criteria

### Verification & Testing
- [ ] `pytest --tb=short -q` runs and reports **0 failures** on all 365+ tests.
- [ ] `python verify_integrity.py` executes successfully.
- [ ] Zero blocking `time.sleep()` calls inside `async def` methods.
- [ ] All inputs and textareas retain logical `dir="auto"` compliance.


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

## 2026-07-10T07:53:48Z

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

### R6. Codebase-wide Hardening & Refactoring
Audit, optimize, and refactor code anomalies listed in `IMPROVE_ME.md`, including converting remaining long functions to modular structures, resolving typing inconsistencies, configuring logging, adding robust exception handling, and resolving hardcoded URLs.

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

### CI/CD Pipeline & Code Health
- [ ] Running `pytest tests/e2e/` passes all tests with zero failures, proving the system is ready for automated Render deployment.
- [ ] All 365+ existing tests pass without regressions, and new tests are added to verify the refactoring improvements.
- [ ] Key architectural refactorings are verified by running `verify_integrity.py` and obtaining a successful exit status.

## 2026-07-10T09:50:06Z

Refactor, document, and harden the core production files of the JobHunt Pro application to resolve critical code quality warnings, missing type hints, long functions, and exception handling while preserving complete compatibility with all tests and Arabic layout constraints.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Production Core Files Refactoring
Refactor the following targeted production files sequentially to address all code quality and warning signals reported in `IMPROVE_ME.md`:
1. `core/email_engine.py` (Decompose long functions, extract hardcoded URLs to `config.py`, add full type hints and docstrings, ensure safe exception handling and loggers).
2. `core/pa_job_scraper.py` (Decompose search methods, extract URL targets to configuration variables, add docstrings and typing).
3. `core/telegram/bot.py` (Resolve missing type hints, decompose bot execution loops and callback query handlers).
4. `web/app_v2.py` (Refactor long routes and table creation logic, add proper type signatures and error boundaries).

### R2. Structural UI & Translation Compliance
Ensure that all layout and translation directives for Arabic support remain intact (e.g., `'Cairo', 'Tajawal'` fonts, base line-heights, logical properties selectors, and contextual `dir="auto"` attributes).

### R3. Test Suite Integrity
Maintain complete parity with the E2E and unit test suite. No modifications should introduce regressions or break existing tests.

## Verification Resources
- Use the existing test suite: `pytest` configured with dynamic mock configurations.
- Use `scripts/auto_improve_loop.py` to compile code quality progress after refactoring.

## Acceptance Criteria

### Test Execution Guardrail
- [ ] `pytest` execution must run and return 100% clean green pass.

### Quality Warning Mitigation
- [ ] Priority scores for the refactored target files in `IMPROVE_ME.md` must be successfully cleared.

## 2026-07-10T18:41:55Z

# JobHunt Pro Swarm Optimization & Cloud Deployment Prompt

Optimize the JobHunt Pro Swarm codebase by implementing core optimizations (RTL, localizations, database connections) and creating configurations for a $0 24/7 permanent cloud deployment.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. RTL & Localization Optimization
Align the front-end layout with Middle East/Gulf guidelines:
- Apply CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline-start/end`) dynamically.
- Set Arabic typography rules on relevant components (Cairo/Tajawal, min font size 15px, line-height 1.7-2.0, zero letter-spacing).
- Configure directional icon flipping and `dir="auto"` on input fields.

### R2. Backend Performance & SQLite to Turso Configuration
- Configure the existing SQLite backend to dynamically connect to a Turso database when `TURSO_DATABASE_URL` is set in the environment.
- Add connection pooling and caching wrappers for database query sessions.

### R3. Free Cloud Deployment Configurations
Generate deployment files targeting $0 free-tier platforms:
- Koyeb configurations/Dockerfiles to run backend APIs (24/7 permanent).
- Hugging Face Spaces configurations/Dockerfiles to run python scrapers/workers (24/7 permanent).
- Cloudflare Pages setup configs to build and serve the Vue frontend.

## Acceptance Criteria

### RTL & CSS Logic
- [ ] Front-end components utilize CSS logical properties rather than physical properties (e.g., `margin-inline-start` instead of `margin-left`).
- [ ] Typography stacks for Arabic languages avoid `letter-spacing` and use line heights between 1.7 and 2.0.

### Database Integration
- [ ] The app dynamically switches to Turso libSQL client if remote credentials are provided, falling back to local SQLite if not.
- [ ] Database calls handle connection pooling correctly under async sessions.

### Deployability
- [ ] Dockerfiles for Koyeb and Hugging Face build successfully.
- [ ] Static deployment config files are valid and readable.

## 2026-07-10T19:52:26Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Analyze and directly enhance the current project located at `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`. Apply comprehensive improvements covering code quality, performance, SEO, modern UI/UX design (respecting Arabic/RTL constraints), and marketing. Additionally, configure the project for a 24/7 permanent cloud deployment strategy that requires absolutely zero financial investment (e.g., setting up GitHub Actions for Vercel/Cloudflare Pages or Oracle Cloud).

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Code, UI, and Performance Enhancements
Directly edit the project files to improve code quality, implement modern design aesthetics, optimize performance, and add SEO best practices. Adhere strictly to the RTL and Arabic typography rules defined in the project's agent instructions.

### R2. Zero-Cost 24/7 Cloud Deployment Configuration
Configure the repository with the necessary files (e.g., `vercel.json`, GitHub Actions workflows, or deployment scripts) to achieve a permanent 24/7 cloud presence with zero financial investment on platforms like Vercel, Cloudflare, or Oracle Always Free.

## Acceptance Criteria

### Project Quality
- [ ] The UI/UX is significantly improved, utilizing modern design and proper RTL layouts.
- [ ] SEO meta tags and structural semantic improvements are implemented.
- [ ] Code is refactored for better performance and maintainability without breaking existing functionality.

### Cloud Deployment
- [ ] Necessary configuration files for a free cloud deployment platform are successfully added to the project.
- [ ] The deployment strategy ensures 24/7 uptime without sleep limitations.


## Follow-up — 2026-07-10T20:43:16Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Optimize JobHunt Pro for 24/7 Permanent $0 Cloud Deployment

JobHunt Pro is a production SaaS job-hunting automation platform. The objective is to further optimize performance, reliability, and security for a $0 budget 24/7 permanent cloud deployment.

Working directory: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`
Integrity mode: development

## Requirements

### R1. Single-Container Web+Worker Fusion
- Merge FastAPI web processes and Celery/background workers into a single-process Docker container (e.g., using python-based task queues or async background tasks) to stay under the 750 free-hour monthly limits on platforms like Render.
- Optimize the memory footprint to remain strictly under 512MB.

### R2. Edge-Cached Semantic Engine & Failover Pool
- Integrate Upstash Redis (free tier) to cache identical Cover Letter generation and ATS matching calculations.
- Implement a multi-provider LLM failover pool (Groq + Gemini API + GitHub Models free tiers) inside `core/llm_provider_pool.py`.

### R3. Stealth Scraping & TLS Fingerprinting
- Upgrade scraping utilities (`core/stealth_http.py`) using `curl_cffi` to spoof Chrome TLS JA3 fingerprints.
- Avoid IP bans by implementing random delays and human mouse movements.

### R4. SMTP Warmup & Telegram Webhook
- Implement a smart warming cron loop in `core/free_smtp_pool.py` to preserve sender reputation.
- Migrate the Telegram Bot from long-polling to webhooks hosted within FastAPI to save system memory.

## Verification & Acceptance Criteria

### Automated Verification
- [ ] Running `pytest tests/e2e/test_r2_dashboard.py` and `pytest tests/test_security_hardening.py` passes with zero failures.
- [ ] Integration test verifies that cached LLM responses are retrieved in < 100ms.
- [ ] Docker image build completes and runs under a 512MB RAM cap.
- [ ] HTTP requests using the new stealth client successfully fetch from `https://bot.sannysoft.com/` without getting flagged.

### Manual Verification
- [ ] Deploying to Render's free tier functions without needing a separate paid worker instance.
- [ ] Telegram bot responds instantly to user webhook requests.

## 2026-07-11T00:05:56Z

Implement a comprehensive suite of zero-investment, 24/7 permanent cloud optimization tricks for the JobHunt Pro platform to improve uptime, prevent container crashes, handle LLM rate limits, and optimize database recovery times.

Working directory: c:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Free Tier Keep-Alive Scheduler
Implement a lightweight background daemon or external GitHub Actions cron configuration that pings the FastAPI `/api/v1/health` endpoint every 10 minutes to prevent Render's free tier web service from sleeping.

### R2. Database Pool Recycling & Connection Warmer
Configure SQLAlchemy connection pool properties (`pool_recycle=280`, `pool_pre_ping=True`) to automatically handle Neon Serverless Postgres DB spin-down and cold starts without throwing `500 Internal Server Error` exceptions.

### R3. Groq LLM Rate-Limit Controller & Free Fallbacks
Add a custom Celery rate-limiting decorator that reads Groq's API rate limit response headers (`x-ratelimit-remaining`, `x-ratelimit-reset`) and dynamically delays requests to avoid `429 Too Many Requests` errors.

### R4. Memory Reclamation and OOM Prevention
Configure Celery's `worker_max_tasks_per_child=10` to periodically recycle workers and reclaim leaked memory, and optimize Python's garbage collection parameters in `start_cloud.py` to stay strictly within Render's 512MB RAM limit.

### R5. Dual-Mode SQLite/Neon Job Dispatcher
Provide a fallback configuration allowing local high-frequency scrapes to queue locally on SQLite before syncing results asynchronously to the main cloud PostgreSQL, bypassing Upstash Redis free tier's 10k request cap.

## Acceptance Criteria

### High Availability and DB Resilience
- [ ] The Render app stays warm 24/7 with health checks responding in <150ms.
- [ ] Neon DB resumes gracefully from sleep with zero connection errors in FastAPI logs.

### Task Queue & LLM Stability
- [ ] High-concurrency matching tasks do not trigger Groq rate limits; the decorator handles retries dynamically.
- [ ] Uvicorn + Celery + SyncWorker container stays below 450MB RSS RAM during high-load scraping.

## 2026-07-11T09:09:27Z

Implement the third set of enterprise-grade security, performance, reliability, and monitoring improvements for the JobHunt Pro platform. Ensure all existing 431 tests continue to pass with zero regressions.

Working directory: c:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi
Integrity mode: development

## Current State

The project currently has:
- **431/431 tests passing** — do NOT regress any existing tests
- JWT Authentication with IP lockout brute-force protection (`backend/auth.py`)
- Redis cache for ATS results (`core/ats_matcher.py`)
- Exponential HTTP backoff for scraping (`core/stealth_http.py`)
- Telemetry & DLQ requeuer endpoints (`backend/main.py`)
- Single-instance supervisor manager (`start_cloud.py`)

## Requirements

### R1. Multi-Key JWT Secret Rotation
Modify `backend/auth.py` to support multiple active JWT secret keys (e.g. read from an environment variable `JWT_SECRET_KEYS` as a comma-separated list). The first key in the list is the primary key used to sign new tokens. When verifying a token, if it fails validation with the primary key, attempt to verify it using the remaining active keys. This allows zero-downtime secret rotation. If `JWT_SECRET_KEYS` is missing, fall back to `JWT_SECRET_KEY` (which itself falls back to the test key in test mode). Write at least 2 unit tests that verify: (a) tokens signed with the old secret still pass verification after a new key is added as primary, (b) tokens signed with an invalid key are rejected.

### R2. Secure CORS Dynamic Origin Validation
Refactor CORS origin handling in `backend/main.py` to securely validate incoming request origins dynamically. Instead of using generic wildcard checks or simple string inclusion, implement a helper that performs strict regex-based origin matching. For instance, if `ALLOWED_ORIGINS` contains `https://*.jobhunt-pro.com`, verify that the incoming origin matches `^https://[a-zA-Z0-9-]+\.jobhunt-pro\.com$`. Wildcards should only be allowed at the subdomain level. Write at least 2 unit tests to verify: (a) valid matching origins (including allowed subdomains) are allowed, (b) malformed origins (e.g. `https://attacker-jobhunt-pro.com`) are rejected.

### R3. Celery Integration & Task Routing Verification
Add integration tests in a new file `tests/test_celery_integration.py` that verify Celery task serialization and routing. Mock the celery broker and check that calls to `scrape_jobs.delay()` and `generate_cover_letter.delay()` properly serialize arguments to JSON and map to their designated queues. Verify that task parameters conform to their expected types.

### R4. SMTP & External API Connection Health Monitor
Extend the detailed health check endpoint `GET /api/v1/health/detailed` in `backend/main.py` to report status of outgoing mail configuration and external API services. It should check: (a) SMTP connectivity by executing a quick TCP connection test to the configured host/port (e.g. Brevo/Gmail), (b) Groq API accessibility via a lightweight check (e.g. a simple GET to their status page or a zero-token request). Ensure these checks have tight timeouts (<1s) and fail gracefully without crashing the endpoint. Write at least 2 tests verifying that SMTP and API statuses are reported in the detailed health check payload.

### R5. Scraper Daily Cap and BanShield Cooldown Enforcement
Harden `core/ban_shield.py` or `core/anti_ban.py` to enforce daily scraping limits and cooldown rules strictly. If the daily cap is exceeded, scraping requests must instantly raise a custom `DailyLimitExceededException` or return a distinct error status instead of attempting the scrape. Write at least 2 unit tests that verify: (a) scraping requests are blocked once the daily cap is reached, (b) the daily counter resets correctly when the day boundary changes.

## Acceptance Criteria

### Security & Authentication
- [ ] JWT verification succeeds for tokens signed with any active secret key in `JWT_SECRET_KEYS`
- [ ] Subdomain wildcards in `ALLOWED_ORIGINS` are matching securely via regular expression validation

### Task Queue & Reliability
- [ ] Celery tasks are verified to serialize args to JSON and route to the correct queues
- [ ] Scraping calls raise a limit exception once the daily cap is reached and reset on day boundary

### Monitoring & Diagnostics
- [ ] `GET /api/v1/health/detailed` reports `smtp` status and `groq_api` status in its response payload

### Test Suite Integrity
- [ ] All 431 pre-existing tests continue to pass
- [ ] At least 10 new tests are added covering the 5 requirements above
- [ ] Run `pytest --tb=short -q` and confirm `0 failed`

## 2026-07-12T11:56:04+03:00

Implement a suite of 0-cost, 24/7 permanent cloud optimizations, performance upgrades, and reliability enhancements for the JobHunt Pro app, selecting high-impact items from `IMPROVEMENTS_MASTER.md` and adding tricks to keep everything running permanently on free-tier cloud infrastructure with 0 investment.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi

## Requirements

### R1. Deploy Frontend to Cloudflare Pages (Free Tier)
- Shift the Vue/Next.js/HTML frontend to Cloudflare Pages (free tier, unlimited bandwidth, global CDN).
- Configure proxy headers so backend API calls (`/api/*`) are correctly routed, offloading all static assets from the Render container.
- Expected improvement: Reduces Render RAM consumption by ~20% and bandwidth egress by ~60%.

### R2. Add Platform-Specific Intelligent Scraper Rate Limit Profiles (Anti-Ban)
- Implement adaptive delays (`core/ban_shield.py` & `core/anti_ban.py`) and platform-specific delay dictionaries.
- Fine-tune delays: LinkedIn (3s delay, random jitter), Indeed (1s), Bayt (2s).
- Expected improvement: Decreases provider block rate by ~80% (improving scraping success rate from ~30% to ~95%+).

### R3. Database Optimization & Bulk Inserts
- Replace loop-based DB insertions in scrapers with SQLAlchemy bulk inserts (`session.execute(insert(Model), [...])`).
- Expected improvement: Accelerates database ingestion speed by ~10x (900% improvement) and lowers database CPU load on Neon.

### R4. SSRF Prevention & Scraper URL Validation
- Validate scraped job URLs against private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`) before performing HTTP requests.
- Expected improvement: Eliminates server-side request forgery vulnerability (100% security improvement).

### R5. persistent logging to logtail (free tier)
- Integrate Logtail (or similar free-tier log drain) into the FastAPI / Render config to ensure logs are preserved beyond the 1-hour Render limit.
- Expected improvement: Increases log retention from 1 hour to 30 days (720x improvement) for debugging.

## Acceptance Criteria

### Performance & Memory Offload
- [ ] Frontend static assets are served from Cloudflare Pages, confirmed via asset headers.
- [ ] Render container RAM usage stays comfortably below the 512MB free tier limit (recycled at 450MB).

### Scraper Stability & Database Speed
- [ ] Scrapers run concurrently without triggering IP bans on Indeed/Bayt due to provider-specific delay profiles.
- [ ] Job ingestion uses batch bulk insertions, verified by database queries/logs.

### Security
- [ ] Scrapers block any attempt to query local/internal URLs, throwing validation errors.

## 2026-07-12T10:19:46Z

JobHunt Pro: Enterprise AI-Powered Job Application Automation Platform. Improve cloud deployment, performance, stealth scraping, and reliability on 100% free tiers.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Cloudflare Pages Next.js Deployment
- Deploy the Next.js frontend code from `frontend/` to Cloudflare Pages (Free Tier).
- Set up proxy routes in `vercel.json` or Cloudflare redirects so `/api/v1/*` routes to the Render FastAPI backend URL.
- Enable CORS credentials and update the allowed origins array in `backend/config.py` to match the Cloudflare Pages domain.

### R2. GitHub Actions Scheduled Keep-Alive (24/7 Free Uptime)
- Create a `.github/workflows/keepalive.yml` workflow that triggers every 12 minutes using GitHub Actions scheduled trigger.
- The workflow should run a simple curl script to ping `/healthz` on the Render backend, keeping the free tier container active 24/7 without consuming Render build minutes.
- Also ping the Neon database warming script/endpoint.

### R3. Celery Memory Guard Configuration
- Modify the Celery command in `start_cloud.py` to run with `--max-tasks-per-child=10` and `--max-memory-per-child=150000` (150MB).
- This ensures worker processes recycle frequently to prevent hitting Render's 512MB RAM OOM limits.

### R4. Neon PgBouncer Connection String Updates
- Adjust database connection initialization in `backend/database.py` and `backend/sync_worker.py` to support Neon PgBouncer connection pooling.
- Append `?sslmode=require&prepareThreshold=0` to database URLs and target port 5432 with pooled host configurations.

### R5. Free Proxy Pool Scraper Rotation
- Implement a background cron or Celery task in `core/ghost_hunter.py` that scrapes free proxy lists (e.g., proxyscrape, free-proxy-list) hourly.
- Validate these proxies and rotate them in the Playwright/Camoufox Stealth scraper to prevent LinkedIn/Indeed IP blocking.

## Acceptance Criteria

### Performance & Memory
- [ ] Frontend successfully runs on Cloudflare Pages with under 1.5s page load times.
- [ ] Render API RAM usage remains under 350MB, with no supervisor process recycling events triggered.

### Uptime
- [ ] Render backend service does not enter sleep mode (0% cold starts during testing).
- [ ] SQLite to Postgres synchronization is fully stable under Neon connection pooling.

### Code Integrity
- [ ] All 403 test suites pass (`python -m pytest tests/ -q`).
- [ ] No hardcoded api keys or secrets.

## 2026-07-12T13:08:58Z

Migrate and optimize JobHunt Pro to ensure 100% free (0 investment) 24/7 cloud uptime without hitches, bypassing Render's free tier limit suspensions by hosting the backend on Hugging Face Spaces (Docker CPU Basic) or GitHub Actions crons, and implementing resource optimizations.

Working directory: `C:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi`

Integrity mode: development

## Requirements

### R1. Hugging Face Spaces (Docker CPU Basic) Backend Migration
Migrate the FastAPI backend and Celery workers to a Hugging Face Space using Docker CPU Basic (2 vCPU, 16GB RAM) which is 100% free. Define a Dockerfile that loads dependencies, installs system requirements (like Chrome/Chromium for scrapers), and starts the FastAPI service.

### R2. GitHub Actions Scheduled Runner Cron
Configure a secondary lightweight cron execution flow using GitHub Actions (2,000 free minutes/month) to run the scraping and applying loop every 30 minutes, bypassing the need for a 24/7 running Celery background worker process.

### R3. DB and Cache Rate-Limit Shield
Add local caching (thread-safe cache) to prevent exceeding Upstash Redis (10k command/day limit) and SQLite fail-safety fallback in case the Neon PostgreSQL database is waking up from sleep.

### R4. Browser Scraper Performance Optimization
Configure Playwright/Camoufox scrapers to block images, media, CSS stylesheets, and trackers to reduce RAM and network bandwidth usage, preventing memory exhaust crashes on free-tier containers.

## Acceptance Criteria

### Deployment & Hosting
- [ ] Backend is runnable in a Docker container suitable for Hugging Face Spaces.
- [ ] GitHub Actions workflow is created under `.github/workflows/scheduled_runner.yml` to run the loop.

### Resource Efficiency
- [ ] Browser scrapers block heavy resources (images, fonts, stylesheets) during execution.
- [ ] Redis commands are cached locally to stay under the 10,000 daily command limit.

## Follow-up — 2026-07-12T13:22:26Z

The user has requested that you keep optimizing the project continuously until there is absolutely nothing left to improve, optimize, or fix. Please ensure that you run exhaustive verification checks and polish the code to a premium level. Do not stop until all requirements are met and the codebase is completely hardened.

## Follow-up — 2026-07-12T13:22:48Z

Please scale up the execution swarm to the absolute maximum concurrency. Spawn parallel worker and testing subagents for Milestones 2, 3, and 4 immediately, so they can progress concurrently instead of sequentially, accelerating the overall migration and optimization process.

## Follow-up — 2026-07-12T13:32:31Z

The user has requested that you also target and implement all the remaining 33 outstanding TODO items listed in the inventory of IMPROVEMENTS_MASTER.md (such as performance optimization, async concurrency caps, database N+1 queries, memory profiling, and bundle analysis). Keep iterating, optimizing, and fixing the entire codebase recursively until there are no items left in TODO and absolutely nothing more can be improved.

## Follow-up — 2026-07-12T13:56:25Z

The user has added these additional feature requirements to the active sweep:
- **R6. AI Model Upgrades**: Integrate fallback/rotation to Gemini 1.5 Pro and Claude 3.5 Sonnet API inside the core LLM provider pool for Cover Letter generation and Resume ATS matching.
- **R7. Next.js Dashboard Analytics**: Build interactive charts/statistics in Next.js showing job search success metrics, email open rates, and ATS score history.
- **R8. Scraper Expansion**: Add at least 3 new GCC/remote-focused boards (e.g. Bayt GCC, GulfTalent, specialized remote portals) to the scraper pool.
- **R9. Auto-Fill Browser Agent**: Implement automated browser autofill scripts for custom job application forms.
- **R10. WhatsApp Bot Remote Control**: Add commands (`/start`, `/pause`, `/status`) to the WhatsApp bot to control campaigns directly from phone.

## Follow-up — 2026-07-12T17:04:36+03:00

The user has consolidated the active sweep into a single, comprehensive Master Plan containing all 10,000+ improvements. You must execute all of these requirements concurrently without waiting:

### Phase 1: Zero-Investment 24/7 Cloud Migration
- Migrate FastAPI/Celery to Hugging Face Spaces (Docker CPU Basic, 16GB RAM).
- Set up scheduled runner crons via GitHub Actions (.github/workflows/keepalive.yml & scheduled_runner.yml).

### Phase 2: DB, Cache & Rate-Limit Shields
- Implement client-side SQLite caching for high-frequency scrapes, syncing asynchronously to Neon PostgreSQL.
- Support PgBouncer connection pooling (`prepareThreshold=0`) and SQLAlchemy connection warmers.

### Phase 3: Browser Scraper & Stealth Optimizations
- Block heavy media/CSS/trackers in Playwright/Camoufox, implement Bezier human mouse curves, and curl_cffi JA3 fingerprinting.

### Phase 4: Remaining 33 Master TODOs
- Resolve all 33 outstanding TODOs in `IMPROVEMENTS_MASTER.md` (concurrency caps, database N+1 queries, memory profiling, bundle optimizations, etc.).

### Phase 5: Next-Level Features
- Add LLM rotation pool (Groq, Gemini 1.5 Pro, Claude 3.5 Sonnet fallback).
- Build Next.js Dashboard Analytics UI showing success rates, open-rates, and ATS history.
- Add GCC scrapers (Bayt GCC, GulfTalent).
- Build browser agent form autofill scripts.
- Add WhatsApp bot remote commands (`/start`, `/pause`, `/status`).

### Phase 6: Enterprise/SaaS & Multi-Tenant Core
- Refactor backend and database to support multi-tenant user accounts with individual CV and SMTP pools.
- Add an AI Interview Prep Simulator endpoint to generate mock interviews based on applied job descriptions.
- Add dynamic tailored PDF resume generation and Chrome Extension endpoints.

Allocate the absolute maximum number of specialized concurrent agents to implement and verify this entire master list in one run.

## Follow-up — 2026-07-12T13:58:32Z

The user has requested to scale up agents even further to accelerate execution. Please spawn specialized parallel worker agents for Milestones 5, 6, 7, 8, and 9 immediately so they can run in parallel alongside Milestones 1-4. Maximize concurrent agent threads to complete the entire backlog as fast as possible.

## 2026-07-12T20:48:30Z

Migrate, optimize, and expand the JobHunt Pro platform into a zero-cost, highly resilient, and commercially scalable multi-tenant SaaS. Bypasses Render's free tier limits, resolves all 20 remaining pending TODOs, adds advanced AI/UI enhancements, and introduces enterprise SaaS features.

Working directory: `C:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi`

Integrity mode: development

## Requirements

### R1. Complete execution of all 20 remaining pending TODOs from IMPROVEMENTS_MASTER.md
Resolve each of the 20 pending TODOs below:
1. **IMP-034**: N+1 query elimination audit (Add selectinload/joinedload where queries loop).
2. **IMP-037**: Next.js bundle analysis (@next/bundle-analyzer to find large chunks).
3. **IMP-038**: Next.js ISR for static job pages (getStaticProps + revalidate:300 for job listing pages).
4. **IMP-039**: Celery task group/chord for bulk email (celery.group() for parallel batch email dispatch).
5. **IMP-095**: Email dispatch E2E tests (aiosmtpd mock SMTP to test send_application_email Celery task).
6. **IMP-097**: Telegram bot command tests (Unit test each bot command handler in isolation).
7. **IMP-099**: Locust load tests (100 concurrent users on /api/v1/jobs/scrape).
8. **IMP-100**: Mutation testing with mutmut (mutmut run on core/scam_detector.py to find weak assertions).
9. **IMP-101**: Frontend snapshot tests (Jest toMatchSnapshot() for key React components).
10. **IMP-102**: API contract tests via Schemathesis (schemathesis run against OpenAPI spec in CI).
11. **IMP-128**: Multi-region DNS failover (Cloudflare health-check-based DNS failover).
12. **IMP-154**: Dead code removal via vulture (vulture . --min-confidence 80).
13. **IMP-158**: Large function decomposition (Decompose functions >100 lines in core/).
14. **IMP-160**: Import sorting with isort (isort . --profile black).
15. **IMP-162**: Dependency version pinning (pip freeze to exact versions in requirements.txt).
16. **IMP-183**: Arabic NLP job matching (AraBERT embeddings for Arabic job-CV similarity).
17. **IMP-187**: User onboarding wizard (Multi-step: upload CV → preferences → email pool → test run).
18. **IMP-190**: LinkedIn OAuth login (LinkedIn OAuth2 via authlib; auto-import profile to CV).
19. **IMP-243**: Streaming cover letter preview (Word-by-word streaming preview in frontend dashboard).
20. **IMP-247**: CV PDF parsing accuracy (Switch from pdfminer to pdfplumber for multi-column CVs).

### R2. Auto-Fill Browser Agent
Create `core/form_autofill.py`:
- Function `autofill_job_form(url: str, user_profile: dict)` using Playwright.
- Navigates to the job application URL.
- Detects form fields (name, email, phone, cover letter textarea).
- Fills them with user_profile data.
- Clicks submit button.
- Returns `{success: bool, screenshot_path: str}`.

## Acceptance Criteria

### Task Completion
- [ ] All 20 remaining TODOs in `IMPROVEMENTS_MASTER.md` are completed and marked as done.
- [ ] Auto-fill browser agent `core/form_autofill.py` is implemented and functional.
- [ ] No regressions: all existing test suites pass with zero failures (`pytest tests/ -q`).

## 2026-07-14T08:13:52Z

Optimize, harden, and synchronize the JobHunt Pro application's frontend and backend systems, ensuring 100% test suite compliance and Gulf-region accessibility.

Working directory: c:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Frontend UI/UX Hardening (RTL & Gulf Region Ergonomics)
- Strict usage of CSS Logical Properties (e.g., `margin-inline-start`, `padding-inline-end`, `inset-inline-start/end`, `inline-size`/`block-size`) across all components.
- Secure implementation of Arabic typography using `'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif` with a minimum font size of `14px` (recommended `16px`) and line heights of `1.6` to `2.0`.
- Explicit elimination of any `letter-spacing` styles on Arabic text elements.
- Directional icons must mirror dynamically based on language using a scalable CSS/JS structure.

### R2. Backend Optimization & API Contract Alignment
- Maintain 100% compliance with established API contracts, including DLQ requeue, Brevo/SendGrid webhook processing, and dashboard statistics queries.
- Ensure strict database connection pooling configurations for Neon (SQLite fallback) preventing connection leaks and cold-start timeouts.
- Hardened security middleware including JWT validation, strict CORS origin regex validation, and rate limiting.

### R3. Test Suite Integrity
- No modifications to the application may break the existing test coverage.
- All 611+ unit, integration, and E2E test cases in the `tests/` directory must compile and pass cleanly.

## Acceptance Criteria

### CSS & Layout Integrity
- [ ] Every modified frontend component strictly uses CSS Logical Properties instead of physical margins/paddings/insets.
- [ ] Arabic views load Cairo font with zero instances of letter-spacing applied.

### Backend & API Stability
- [ ] Swagger OpenAPI specs build correctly and align with all endpoints.
- [ ] Database query tracing shows zero N+1 bottlenecks in dashboard stats fetching.

### Verification Run
- [ ] Command `python -m pytest` executes successfully with 100% passing rate.
- [ ] Frontend builds successfully using `npm run build` in the `frontend` directory.

## 2026-07-14T11:39:54Z

Complete frontend and backend optimization of JobHunt Pro. This includes perfecting UI/UX for all 70+ template pages and the Next.js app, optimizing FastAPI router logic/SQLite database performance, and ensuring the entire 608 test suite passes.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Frontend UI/UX Overhaul & RTL Focus
- Complete and polish all 70+ HTML templates in `web/templates` and the Next.js frontend code in `frontend/`.
- Ensure strict adherence to Arabic and RTL layout guidelines:
  - Use CSS Logical Properties (e.g., `margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `inline-size`).
  - Set Arabic typography with fonts 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif, minimum size 14px (recommended 16px), line-height 1.6 to 2.0, and no letter-spacing.
  - Implement cultural ergonomics color coding: Green for success, Black/Gold for luxury, Blue for trust, Red for strict errors.
  - Add dir="auto" on all form inputs.
  - Apply directional mirroring to icons using --text-x-direction.
- Resolve all visual bugs, formatting issues, responsive design flaws, and missing translations.

### R2. Backend Router & DB Optimization
- Optimize the FastAPI backend (web/app_v2.py and routers under web/routers/).
- Streamline DLQ requeue logic, webhook routers (Brevo, SendGrid), and dashboard stats query performance.
- Address any database query bottlenecks and optimize indices for SQLite database interactions (jobhunt_saas_v2.db).

### R3. Test Suite Integrity
- Maintain correctness of all existing features.
- Ensure that the entire suite of 608 pytest tests passes successfully after optimizations.

## Acceptance Criteria

### Frontend Quality & Layout
- [ ] Every modified HTML template file uses CSS Logical Properties instead of physical properties (e.g., no margin-left or padding-right in CSS).
- [ ] Arabic typography is applied everywhere with a font family list starting with 'Cairo', and font size is never below 14px.
- [ ] All input fields in forms have the dir="auto" attribute.
- [ ] Next.js app builds cleanly without compilation or ESLint errors.

### Backend & Database Performance
- [ ] The DLQ requeue endpoint (/api/v1/admin/dlq/requeue) behaves correctly according to the interface contract.
- [ ] Webhook endpoints for Brevo and SendGrid process events efficiently and correctly.
- [ ] Query times on dashboard stats api endpoints are minimized and SQLite database locks/bottlenecks are resolved.

### Test Verification
- [ ] Running pytest runs and passes all 608 test cases.


## Follow-up — 2026-07-14T15:54:14+03:00

Verify and audit the complete frontend templates (logical properties, RTL alignment, typography) and backend routes (database connections, API contract, test pass status) for JobHunt Pro.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Frontend Validation & Accessibility Audit
- Audit all 114 HTML templates under `web/templates` and the Next.js app in `frontend/` to confirm that:
  - Every modified CSS class/attribute uses logical properties (`margin-inline-start`, etc.) instead of physical ones.
  - Arabic typography is clean, uses the `'Cairo'` font, has a minimum size of `14px`, and does not apply `letter-spacing`.
  - All form inputs, textareas, and select elements have the `dir="auto"` attribute.
- Ensure that the Next.js build runs cleanly without errors.

### R2. Backend & API Stability Verification
- Validate that all backend FastAPI routers are free of runtime bugs, undefined variable warnings, or unresolved syntax.
- Verify that Neon/SQLite database connection pooling works properly, connection leaks are prevented, and endpoints align with their respective interface contracts.

### R3. Test Suite Verification
- Run the full pytest suite and guarantee that all 614 tests pass successfully.

## Acceptance Criteria

### Verification & Compliance
- [ ] 100% of the 614 unit/E2E tests pass without failures.
- [ ] No undefined variable errors (F821) exist in python codebase.
- [ ] All template files are checked for logical properties compliance and verified.

## Follow-up — 2026-07-14T13:52:48Z

Enhance, audit, and fix the JobHunt Pro application across both frontend and backend to achieve clean API execution, zero database connection leaks, flawless bilingual RTL/Arabic and LTR/English layouts, and 100% test coverage compliance (614 tests passing).

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Frontend Compliance, RTL & Typography Auditing
- **CSS Logical Properties**: Modify/confirm styling across the 114 HTML templates (under `web/templates`) and the Next.js application (`frontend/`) to strictly use CSS Logical Properties:
  - `margin-left` -> `margin-inline-start`
  - `padding-right` -> `padding-inline-end`
  - `left`/`right` -> `inset-inline-start`/`inset-inline-end`
  - `width`/`height` -> `inline-size`/`block-size`
- **Arabic Typography**: Check and enforce that Arabic text uses 'Cairo', 'IBM Plex Arabic', or 'Tajawal' fonts with a minimum size of 14px, line-height between 1.6 and 2.0, and strictly no letter-spacing.
- **Forms directionality**: Ensure all <input>, <textarea>, and <select> elements use dir="auto".
- **Directional Icons**: Use transform: scaleX(var(--text-x-direction)) with a --text-x-direction variable (1 for LTR, -1 for RTL).
- **Next.js Production Build**: Verify that the Next.js app in frontend/ builds cleanly.

### R2. Backend & API Stability & DB Connection Pooling
- **FastAPI Routers**: Review all router modules in web/routers/ and the main entry point web/app_v2.py. Fix any undefined variables (flake8 F821), runtime bugs, or unhandled exceptions.
- **Database Connection Pooling**: Ensure that database connections/pooling for both Neon Postgres and SQLite are handled efficiently, preventing any connection leaks.
- **Interface Contracts**: Align DLQ, Webhook, and Dashboard Stats endpoints with their defined API contracts.

### R3. Test Suite Verification
- Verify that the entire pytest suite of 614 tests passes without any errors or regressions.

## Acceptance Criteria

### Technical & Verification Checklist
- [ ] 100% Test Success: Running pytest runs and passes all 614 tests with 0 failures.
- [ ] Zero Linter Errors: No undefined variable warnings (F821) in the python files.
- [ ] Next.js Build: Running Next.js build script npm run build inside frontend/ completes successfully.
- [ ] Logical Properties Audit: All HTML templates under web/templates are compliant with CSS Logical Properties and Arabic typography standards.
- [ ] Connection Pooling: Database pool connections are correctly released, verified via integration/concurrency tests.

## Follow-up — 2026-07-14T19:23:44Z

Complete A-to-Z audit, optimization, and alignment of the JobHunt Pro enterprise application. Polish and secure the FastAPI backend, optimize database queries/connections, and resolve all RTL/Arabic and LTR/English page layouts across all 70+ templates and Next.js frontend, ensuring 100% of the 614+ test suite passes.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: benchmark

## Requirements

### R1. Backend & Database Integrity
Ensure FastAPI routers (`web/routers/*`, `web/app_v2.py`) compile and execute cleanly with no database connection leaks. Use strict context management or decorators for sessions. Ensure database pooling survives cold starts (supporting Neon PostgreSQL and SQLite fallbacks).

### R2. Flawless Bilingual UI/UX and CSS Logical Properties
Audit and polish all 70+ HTML templates in `web/templates/` and `web/templates/en/` and the Next.js app (`frontend/`). All pages must use CSS Logical Properties (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`, etc.) to prevent layout breakage on theme/locale shifts. Arabic text must use Cairo/IBM Plex Arabic fonts, line-height 1.6-2.0, with no letter-spacing. All form inputs must have `dir="auto"`.

### R3. API Security and Contract Compliance
Enforce strict JWT Bearer token authentication on all `/api/v1/*` endpoints, returning `401 Unauthorized` for missing/invalid tokens. Ensure proper CORS and IP rate limiting (brute-force protection).

### R4. Full Test Suite Success
Execute all pytest test cases in `tests/` and verify that 100% of them pass without a single bypass, skip, or failure.

## Acceptance Criteria

### Backend & DB Quality
- [ ] No database connection leaks are left in any API routers or background scripts under stress testing.
- [ ] API responses use versioned paths and enforce strict type schemas.

### RTL & Logical Properties Compliance
- [ ] No hardcoded directional CSS properties (like `margin-left` or `padding-right` or `left`/`right`) in any page templates or frontend components.
- [ ] Arabic typography follows rules: `'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif` is used, min font-size is 14px, line-height is 1.6-2.0, and letter-spacing is removed.
- [ ] Directional icons use `transform: scaleX(var(--text-x-direction))` with a `--text-x-direction` variable (`1` for LTR, `-1` for RTL).

### Frontend Production Build
- [ ] Next.js build (`npm run build` inside `frontend/`) completes with zero TypeScript or compilation errors.

### Pytest Suite Validation
- [ ] Running `python -m pytest tests/` returns `0` exit code, indicating all 614+ test cases passed successfully.

## 2026-07-15T06:31:31Z

# Teamwork Project Prompt

Complete A-to-Z audit, optimization, and alignment of the JobHunt Pro enterprise application (frontend and backend).

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi

## Requirements

### R1. Complete Frontend and Backend Audit & Improvement
Perform a thorough, comprehensive sweep across the entire application (including frontend components, page templates, routing, and backend systems) to fix styling, optimize performance, and align features.

### R2. Arabic RTL and Gulf Accessibility Alignment
Ensure all UI pages strictly follow CSS logical properties, Arabic typography rules (Cairo/Tajawal fonts, minimum font size 14px/16px, line height 1.6-2.0, no letter-spacing), and cultural ergonomics (directional icons, RTL scaling, centered/natural primary CTAs).

## Acceptance Criteria

### Audit & Optimization Verification
- [ ] No placeholder or TODO comments remain in the audited files.
- [ ] All pages (approx. 70 Jinja2 templates and React/Next.js pages) compile, load, and render correctly without errors.
- [ ] Backend routes and database interactions work reliably without failing tests.

## Follow-up — 2026-07-15T06:51:48Z

# Teamwork Project Prompt

Complete A-to-Z audit, optimization, and alignment of the JobHunt Pro enterprise application (frontend and backend).

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi

## Requirements

### R1. Complete Frontend and Backend Audit & Improvement
Perform a thorough, comprehensive sweep across the entire application (including frontend components, page templates, routing, and backend systems) to fix styling, optimize performance, and align features.

### R2. Arabic RTL and Gulf Accessibility Alignment
Ensure all UI pages strictly follow CSS logical properties, Arabic typography rules (Cairo/Tajawal fonts, minimum font size 14px/16px, line-height 1.6-2.0, no letter-spacing), and cultural ergonomics (directional icons, RTL scaling, centered/natural primary CTAs).

## Acceptance Criteria

### Audit & Optimization Verification
- [ ] No placeholder or TODO comments remain in the audited files.
- [ ] All pages (approx. 70 Jinja2 templates and React/Next.js pages) compile, load, and render correctly without errors.
- [ ] Backend routes and database interactions work reliably without failing tests.

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

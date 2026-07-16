# Original User Request

## Initial Request — 2026-07-14T10:30:14+03:00

Optimize and improve the frontend and backend of the JobHunt Pro application to resolve performance bottlenecks, enhance user experience, and ensure clean API execution.

Working directory: c:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Frontend UI/UX Enhancement
* Improve the layout of the user dashboard and landing pages using CSS logical properties and modern styling tokens (glassmorphism, clean typography, responsive design).
* Maintain support for bilingual (RTL Arabic / LTR English) visual layouts.

### R2. Backend Router Optimization
* Refactor database access and query handling inside web routers to ensure responsive latency.
* Ensure robust error boundaries and clean logging across all system endpoints.

### R3. Backward Compatibility
* Retain full compatibility with existing SQLite schemas and the tenant management flow.

## Acceptance Criteria

### Verification
- [ ] Run `pytest` and verify that all 608 test cases pass successfully with zero failures.
- [ ] Run the server and verify that the OpenAPI Swagger schema compiles without errors.
- [ ] Visual audit confirms that alignment and typography respect Middle East regional variables.

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

## Follow-up — 2026-07-15T10:11:11+03:00

Full optimization and production-hardening of the JobHunt Pro SaaS platform, achieving all planned milestones (M1-M5) across database performance, email delivery, web scraping reliability, RTL/Arabic UI compliance, and E2E testing.

Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Integrity mode: development

## Requirements

### R1. Pytest E2E Test Suite Hardening
Execute the pytest suite (608 tests), inventory status across all tiers, identify and fix failing/flaky tests, and run adversarial tests (Tier 5) to audit system security.

### R2. Backend Router & DB Optimization
Optimize dashboard stats API endpoints (`/api/v1/dashboard/stats`), DLQ requeue logic, and webhook processors. Tune Neon PostgreSQL and SQLite connections, add indexes on frequently filtered fields, and eliminate N+1 query overhead.

### R3. RTL Arabic UI & Template Polish
Overhaul all 70+ Jinja2 HTML templates in `web/templates/` and Next.js components in `frontend/` to strictly use CSS logical properties (e.g., margin-inline, padding-inline, inset-inline) and Arabic-friendly typography ('Cairo', 'IBM Plex Arabic', 'Tajawal').

### R4. Scraper Resilience & Stealth Configuration
Verify coordinated platform-specific rate limits, residential proxy fallback chains, CAPTCHA solvers, and anti-ban delay shields to ensure stable web scraping with zero downtime.

## Acceptance Criteria

### Testing & Quality
- [ ] All 608 pytest cases run and pass successfully in the local python environment.
- [ ] Mypy static analysis returns zero errors on modified modules.
- [ ] Ruff strict linter passes with zero issues.

### Performance & Database
- [ ] Database query speeds for dashboard statistics improve by at least 80% (measured via Locust/performance scripts).
- [ ] Zero database connection exhaustion issues under simulated peak load.

### RTL Arabic UI
- [ ] Next.js front-end compiles cleanly (`npm run build`) without TypeScript or styling issues.
- [ ] No hardcoded physical alignment directions (left/right) are used in UI templates; only CSS logical properties.

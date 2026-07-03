# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Teamwork optimization in progress

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

---
*Next: when approved → delegate via invoke_subagent (see Delegation Protocol)*

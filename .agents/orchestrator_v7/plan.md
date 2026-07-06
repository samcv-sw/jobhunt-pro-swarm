# Concrete Execution Plan

This plan is structured to execute the 5 milestones to fulfill R1 through R5.

## Phase 1: Exploration
- **Objective**: Run existing test suite and inspect the codebase for any issues, conflicts, or existing implementations.
- **Verification**: Run `pytest tests/e2e/` to identify the baseline state of failures.

## Phase 2: Implementation & Verification of R1-R4
- **Milestone 1**: Frontend UI/UX & RTL Polish
  - Action: Update `globals.css` with font variables, line-height 1.8, and remove physical directions. Update `layout.tsx` to load Cairo/Tajawal fonts and set `dir="auto"`. Update `page.tsx` inputs to have `dir="auto"`.
- **Milestone 2**: Backend Concurrency & Database Sync
  - Action: Modify `backend/sync_worker.py` to handle `asyncpg.PostgresConnectionError` and ensure Celery task dispatches do not block event loop.
- **Milestone 3**: Scraper Stealth Hardening
  - Action: Upgrade `stealth_ingest.py` to support `STEALTH_PROFILES`, random/fallback proxies, and return a structured list of dictionaries with `title` and `url`.
- **Milestone 4**: Security Hardening
  - Action: Ensure all `/api/v1/*` endpoints verify JWT Bearer tokens. Add token verify/issue endpoints in backend.

## Phase 3: E2E and CI/CD Verification
- **Milestone 5**: CI/CD & E2E Validation
  - Action: Create/verify `.github/workflows/production.yml` with correct Python 3.12, Node 20, checkout v4, python setup v5, node setup v4 actions. Run complete test suite and assert 100% passes.

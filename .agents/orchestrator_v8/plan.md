# plan.md — Concrete Execution Plan

This plan outlines the verification, auditing, hardening, and optimization process for JobHunt Pro across all 5 requirements in benchmark integrity mode.

## Phase 1: Exploration & Diagnostics
- **Explorer**: Spawn `teamwork_preview_explorer` to inspect files:
  - `frontend/src/` for any physical CSS properties or build configuration issues.
  - `backend/sync_worker.py` and `backend/main.py` for connection retry logic and Celery blocking queries.
  - `scrapers/stealth_ingest.py` to ensure it returns parsed structured lists of dicts.
  - JWT Bearer auth verification logic on `/api/v1/*`.
  - `.github/workflows/production.yml` for validity.
- **Worker E2E Check**: Spawn `teamwork_preview_worker` to run:
  - `pytest tests/e2e/` to check tests.
  - `npm run build` in `frontend/` to confirm Next.js builds successfully.
  - Profile startup or search queries if needed.

## Phase 2: Bug Fixes & Hardening (if any issues found)
- **Worker**: Spawn `teamwork_preview_worker` to fix any bugs identified in Phase 1.
- **Verification**: Run build and tests.

## Phase 3: Review & Verification
- **Reviewer**: Spawn `teamwork_preview_reviewer` to check code quality and correctness.
- **Challenger**: Spawn `teamwork_preview_challenger` to stress-test security, concurrency, and scraper.
- **Auditor**: Spawn `teamwork_preview_auditor` to run the Forensic Audit check and ensure no integrity issues.

## Phase 4: Final Synthesis & Reporting
- Synthesize all findings and report to the caller agent.

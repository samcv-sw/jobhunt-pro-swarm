# Original User Request

## 2026-07-03T18:48:28Z

You are the Backend Optimization Sub-orchestrator.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_backend_v5
Your mission is to fulfill the requirements in your SCOPE.md:
- Audit FastAPI and Celery integration to guarantee zero blocking on the main event loop (under 50ms).
- Harden database sync_worker.py to catch asyncpg.PostgresConnectionError with a retry mechanism and log appropriately.
- Protect all API endpoints (especially /api/v1/*) with JWT Bearer authentication, returning 401 Unauthorized on missing/invalid credentials.
- Verify changes by running E2E backend/auth tests (pytest tests/e2e/test_database.py, test_e2e_backend.py, test_r4_auth.py).

Follow the Orchestrator Procedure (Assess -> Decompose or Iterate).
Initialize your coordination files (plan.md, progress.md, context.md, BRIEFING.md) in your working directory.
Set up a heartbeat cron (schedule tool, every 10 min) to update progress.md.
Run the Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop.
Use Integrity Mode: benchmark. The Auditor is non-skippable and has a binary veto.
Verify that the concurrency and connection resilience are properly validated.
Once complete, write your handoff.md and send a completion message to the parent conversation ID: 94be6c4d-8896-42dc-bdf5-54497fc84810.

## 2026-07-03T12:41:31+03:00
You are the replacement worker `worker_e2e_setup_gen2` for the JobHunt Pro E2E Testing Track.
Your working directory is: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_e2e_setup_gen2`
The project root is: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`

### MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Objective
1. Inspect the codebase, locate the active Python virtual environment (e.g., check if `.venv2`, `test_env`, or `test_env_2` has `pytest` installed, or look at what environments exist in the project root).
2. Complete and verify the E2E testing files under `tests/e2e/` to cover Tiers 1-4.
3. Specifically, create `tests/e2e/test_database.py` to test the database sync worker and local SQLite configuration. It must test:
   - That local SQLite runs in WAL mode (`PRAGMA journal_mode;` returns `wal` and `PRAGMA foreign_keys;` returns `1`).
   - That `sync_outbox_to_cloud` in `backend/sync_worker.py` successfully queries unsynced records, pushes them to cloud DB, and updates their `synced` flag in SQLite to `True`. Mock `asyncpg.connect` to avoid depending on an actual remote Postgres instance.
   - That the sync worker handles Postgres connection errors gracefully without crashing the loop (e.g., catching postgres connection errors, logging a warning, and sleeping).
   - Test CRUD outbox operations (INSERT, UPDATE, DELETE) and verify payload structure.
4. Expand `tests/e2e/test_frontend.py` and `tests/e2e/test_backend.py` to ensure proper Tier 1-4 test coverage:
   - In `test_frontend.py`, add tests for Arabic font hierarchy and readability (min font-size, line-height 1.6-2.0, no letter-spacing in Arabic classes), form input contextual direction (`dir="auto"`), and mirroring.
   - In `test_backend.py`, add tests for Celery task routes (verifying `scrape_jobs` routes to `scraping`, `generate_cover_letter` to `ai_inference`, and `send_application_email` to `email_sender`), validation errors on endpoints (non-blocking for malformed inputs), and celery task retrying configurations.
   - Add integration/cross-feature tests verifying the flow: FastAPI endpoint call -> inserts outbox record -> sync worker processes record -> Postgres update.
5. Execute the E2E tests using the correct pytest command and virtual environment. Ensure all tests run and pass.
6. Create `TEST_INFRA.md` at the project root detailing the E2E test philosophy, feature inventory, test architecture, and coverage thresholds.
7. Create `TEST_READY.md` at the project root containing the test runner command, coverage summary, and features checklist.
8. Write a handoff report in `.agents/worker_e2e_setup_gen2/handoff.md` summarizing your achievements, showing passing build/test results, and verifying layout compliance.
9. Update your `progress.md` file regularly.

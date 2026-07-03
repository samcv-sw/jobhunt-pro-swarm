## 2026-07-03T08:24:01Z
You are a teamwork_preview_worker.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_e2e_setup
Your task is to execute Milestone 1 (Test Harness Initialization) and Milestone 2 (Tier 1 tests implementation) for JobHunt Pro.

### Objective
1. Initialize the E2E testing framework in a directory named `tests/e2e` inside the workspace `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`.
2. Write Tier 1 Feature Coverage tests to verify the core acceptance criteria of JobHunt Pro:
   - **Frontend UI/UX**: Check that `frontend/src/app/globals.css` and `frontend/src/app/page.tsx` strictly avoid physical directional CSS styles (no `margin-left`, `margin-right`, `padding-left`, `padding-right`, `left:`, `right:` in globals.css declarations). Verify the presence of `.glass-panel` layout, glassmorphism theme, Arabic/RTL support (Cairo/Tajawal fonts in variables, scaleX mirroring helper, dynamic `dir` attribute).
   - **Backend Concurrency**: Verify that the FastAPI backend (`backend/main.py`) queues Celery tasks without blocking the main event loop. Write tests that mock Celery's `.delay()` method and verify it is queued non-blockingly, or configure test clients to send requests concurrently and assert low latency.
   - **Database Sync**: Verify that the database session uses WAL mode on local SQLite databases (`jobhunt_local.db`) and the sync worker `backend/sync_worker.py` can fetch unsynced records from the `ps_crud_outbox` table, process them, and mark them `synced = True`.

### Tasks & Outputs
1. Check the python virtual environment. If test packages (like `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`, `sqlalchemy`, `aiosqlite`) are not installed, install them using the appropriate package tools.
2. Initialize `tests/e2e` and write test files (e.g. `tests/e2e/test_frontend.py`, `tests/e2e/test_backend.py`, `tests/e2e/test_database.py`).
3. Run the E2E tests using `pytest` and confirm they pass.
4. Write a handoff report at `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_e2e_setup\handoff.md` with command invocation details and pass/fail statistics.

### MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

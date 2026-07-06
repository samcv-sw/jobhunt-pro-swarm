## 2026-07-03T21:46:10Z
You are a Worker agent. Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_overdrive_1.

Your task is to apply specific fixes to the codebase to secure the platform and ensure that running `pytest tests/e2e/` directly from the project root succeeds with all 77 tests passing.

Specifically, perform the following edits:
1. In `pytest.ini`, add `pythonpath = .` to the end of the file.
2. In `backend/billing.py`:
   - Import `verify_jwt` from `backend.auth` (e.g., `from backend.auth import verify_jwt`).
   - Secure the checkout endpoint `@router.post("/api/v1/checkout")` by adding JWT verification dependency: `@router.post("/api/v1/checkout", dependencies=[Depends(verify_jwt)])`.
3. In `backend/sync_worker.py`:
   - Locate the main try-except block in `sync_outbox_to_cloud`.
   - Update the catch block to catch both `asyncpg.PostgresError` and `asyncpg.PostgresConnectionError`: `except (asyncpg.PostgresError, asyncpg.PostgresConnectionError) as e:`.
4. Run `pytest tests/e2e/` from the root directory using terminal commands to verify that all 77 E2E tests pass successfully without any module path errors.
5. Write a handoff report to c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_overdrive_1\handoff.md summarizing what files you changed, the exact commands you ran, and their outcomes.
6. Notify your parent (main agent / orchestrator) via send_message when done.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

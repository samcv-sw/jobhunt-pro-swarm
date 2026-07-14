## 2026-07-10T21:16:58Z
You are teamwork_preview_worker.
Your role is to implement the database connection pooling and recycling modifications for Milestone 2, and verify that they pass all unit tests.

Your identity:
- Archetype: teamwork_preview_worker
- Role: Milestone 2 Worker
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m2_dbrecycle

Requirements:
- Enforce strict compliance with c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\AGENTS.md guidelines.
- Apply the proposed modifications from the Explorer's report (`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_dbrecycle\handoff.md`):
  1. In `backend/database.py`: Change `pool_recycle` from `1800` to `280` in the PostgreSQL connection block.
  2. In `core/database.py`: Replace `NullPool` with a resilient `QueuePool` configuration setting `pool_size=3`, `max_overflow=7`, `pool_timeout=15`, `pool_recycle=280`, and `pool_pre_ping=True`.
  3. In `core/pg_sqlite_shim.py`: In `PgConnectionWrapper.__init__`, implement custom connection recycling (discarding connections older than 280 seconds) and connection testing (pre-pinging with "SELECT 1" and discarding stale connections) inside the checkout loop.
- Execute unit and integration tests (`pytest tests/test_pg_shim.py` and the full suite) using your command running tools to ensure no regressions.
- Write your handoff.md detailing the modifications made and the test results.
- Update your progress.md inside your folder.
- When done, send a message back to parent (ID: fa9b20fb-0399-49b4-abb8-cb3e569a72a4) claiming completion.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

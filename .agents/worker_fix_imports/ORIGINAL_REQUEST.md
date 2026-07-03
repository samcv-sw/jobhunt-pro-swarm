## 2026-07-03T11:49:53Z
You are teamwork_preview_worker.
Your workspace directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi
Your metadata/working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_fix_imports

Task:
Please implement the following:
1. Edit core/pg_sqlite_shim.py to add standard PEP 249 database module constants and exceptions to fix the import errors in tests:
   apilevel = "2.0"
   threadsafety = 1
   paramstyle = "qmark"
   Warning = real_sqlite3.Warning
   DataError = real_sqlite3.DataError
   Ensure these are correctly placed near the bottom of core/pg_sqlite_shim.py where standard exceptions are exposed.
2. Run pytest to check if all tests collect and run:
   - PYTHONPATH=. pytest tests/
   - PYTHONPATH=. pytest tests/e2e/
   Record the output of these test commands.
3. Verify Next.js builds:
   - cd frontend; node node_modules\next\dist\bin\next build
   Record the output.
4. Write your findings and result details to: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_fix_imports\handoff.md

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.

Use send_message to notify completion and findings.

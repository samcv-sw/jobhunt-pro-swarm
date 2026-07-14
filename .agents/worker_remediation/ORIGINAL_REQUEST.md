## 2026-07-14T08:19:44Z
You are worker_remediation. Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_remediation.

Your task is to implement the database and security optimization fixes:

1. DATABASE FIXES (reference c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_2\proposed_fixes.patch):
   - In `core/database.py`:
     - Fix the generator yield retry bug: execute connection validation (e.g. `session.execute(text("SELECT 1"))`) prior to yielding, close session on retry failure, yield and clean up session inside a try/finally block.
     - Add local SQLite fallback logic if DATABASE_URL is not set or is SQLite.
     - Set pool size and overflow for Neon PostgreSQL to 2 to stay within the 10-connection limit.
   - In `core/async_db.py`: Set max pool size to 3 and disable statement caching (`statement_cache_size=0`) to ensure PgBouncer transaction mode compatibility.
   - In `web/shared.py`: Remove redundant SQLAlchemy engine and pool creation (`_pg_engine`).
   - In `core/pg_sqlite_shim.py`:
     - Add `__enter__` and `__exit__` context manager wrapper methods on `PgCursorWrapper` to close cursor automatically.
     - Maintain a list of open cursors on `PgConnectionWrapper`, append created cursors to it, and close all open cursors inside `close()` before returning the connection to the pool.
   - In `backend/sync_worker.py`: Retry on PostgreSQL connection/timeout error on cold start, and specify a 10s connection timeout.

2. SECURITY FIXES:
   - In `backend/limiter.py`: Import `_get_client_ip` from `backend.auth` and use it inside `__call__` to resolve client IP safely, preventing header spoofing rate-limit bypass.
   - In `backend/main.py`:
     - Update `_build_origin_regex` to reject TLD wildcards like `*.com` by requiring at least two dot-separated labels after the wildcard (use pattern like `^https?://\*\.[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$`).
     - Remove the insecure hardcoded `https://*.pages.dev` auto-appending from origins list.
     - Update `/ws/war-room` WebSocket route to enforce JWT authentication lockout: retrieve client IP via `_get_client_ip`, verify lockout status with `_check_lockout`, call `_record_success` on success, and call `_record_failure` on JWT exceptions or invalid user subject. Close websocket connection with appropriate code.
   - In `backend/auth.py`:
     - Modify the brute-force tracker `_rate_state` (defaultdict) to evict expired records (with no failures in sliding window and no active lockout) inside `_check_lockout`, `_record_failure`, and `_record_success` to prevent unbounded memory growth.

3. VERIFICATION:
   - Run the full test suite and confirm all tests compile and pass.
   - Run `npm run build` in the `frontend` directory to ensure it builds successfully.
   - Verify that `verify_integrity.py` passes.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write a structured handoff.md inside your working directory summarizing your changes, test outcomes, and verification results.

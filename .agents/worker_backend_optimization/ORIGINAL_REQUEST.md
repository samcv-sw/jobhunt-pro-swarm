## 2026-07-14T07:37:49Z
You are the Backend Optimization Worker for JobHunt Pro.
Your working directory is: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_backend_optimization

Your task is to refactor and optimize the backend routers and database query patterns:

1. DLQ Requeue Endpoint (in `backend/main.py`):
   - Refactor `dlq_requeue` to fix the table name `sync_outbox` -> `ps_crud_outbox`.
   - Optimize the N+1 query loop to a single bulk update. Touch the `created_at` field by setting it to the current time to signal a fresh attempt (e.g., `UPDATE ps_crud_outbox SET synced = 0, created_at = :now WHERE id IN :sids`).

2. Email Bounce Webhooks (in `backend/main.py`):
   - Refactor `brevo_bounce_webhook` and `sendgrid_bounce_webhook` to move database session creation and commit OUTSIDE the event loops. Use a single async session context and single transaction commit per request.

3. Database Indexing:
   - Index the `referred_by` column in the `User` model (`backend/models.py`).
   - Add `CREATE INDEX IF NOT EXISTS idx_applications_tracking_id ON applications(tracking_id);` after the `applications` table creation in `web/app_v2.py` and inside `core/db_migrations/001_performance_indices.sql`.

4. Dashboard Statistics Endpoint (in `web/routers/dashboard.py`):
   - Combine the multiple sequential SQLite queries for campaigns into a single query using conditional aggregation (`SUM(CASE WHEN ... THEN 1 ELSE 0 END)`), reducing connection roundtrips.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

After making the edits, run the build/tests (using `pytest`) to verify all affected target unit tests pass and that there are no regressions. Save a summary of your changes and test/build verification commands and outputs in C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_backend_optimization\handoff.md.
Once complete, send a message back to the parent (id: 50dfdad3-d1a1-4c62-9adb-8213270599fb) with the path to your handoff.md and a brief summary of your verification results.

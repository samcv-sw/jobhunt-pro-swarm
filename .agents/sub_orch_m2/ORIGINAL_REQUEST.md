# Original User Request

## Initial Request — 2026-07-15T10:22:35+03:00

You are a sub-orchestrator (archetype: teamwork_preview_orchestrator) executing Milestone 2.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m2
Your parent is the Project Orchestrator (conversation ID: 8496b1ce-d611-40c6-83f9-ee77f69d9039).
Your mission is: Backend Router & DB Optimization (Milestone 2).

Please perform the following steps:
1. Initialize plan.md, progress.md, context.md, and SCOPE.md in your working directory (.agents/sub_orch_m2).
2. Scan the database layers (e.g. core/database.py, backend/database.py, core/pg_sqlite_shim.py), the dashboard stats routers, the DLQ requeue endpoints, and the Brevo/SendGrid webhook processors.
3. Identify performance bottlenecks, N+1 queries, SQLite/PostgreSQL connection tuning issues, and missing database indexes on filtered fields (e.g. user_id, campaign_id, timestamp).
4. Spawn a Worker (teamwork_preview_worker) to:
   - Optimize the dashboard stats endpoint (/api/v1/dashboard/stats) to eliminate N+1 queries and utilize database-level caching/aggregations.
   - Tune connection pools (Neon PostgreSQL/SQLite) and set connection recycling/age parameters (e.g. 280s age threshold, WAL-mode for SQLite) to prevent connection leaks/exhaustion.
   - Add indices on frequently filtered fields.
   - Optimize DLQ requeue logic and Brevo/SendGrid webhook routers.
   - Run verification builds and tests.
5. Run the performance scripts or Locust tests to verify database query speed improvement of at least 80% for dashboard statistics, and verify zero connection leaks under peak load.
6. Verify that all 626 pytest cases pass successfully.
7. Write your handoff.md in your working directory and notify the parent orchestrator (conversation ID: 8496b1ce-d611-40c6-83f9-ee77f69d9039) using send_message.

MANDATORY INTEGRITY WARNING to include in your Worker/Explorer dispatch:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

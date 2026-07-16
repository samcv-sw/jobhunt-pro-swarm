# Scope: Milestone 2 — Backend Router & DB Optimization

## Architecture
- **Web App / REST API**: FastAPI based backend, exposing dashboard statistics, DLQ requeue, and webhook endpoints (Brevo/SendGrid).
- **Database Access**: Uses PostgreSQL (Neon) and SQLite with a shim layer (`core/pg_sqlite_shim.py`). Connection pooling and query execution are managed here.
- **Data Flow**: Web requests trigger DB queries. Highly-accessed dashboard statistics require optimized queries (avoiding N+1 queries, using caching or database aggregations).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Scan Codebase | Scan and identify connection parameters, index candidates, N+1 queries, DLQ and webhook bottlenecks | None | DONE |
| 2 | Implementation | Spawn worker to optimize stats endpoint, tune pool parameters, add indices, optimize DLQ/webhooks | 1 | DONE |
| 3 | Performance Verification | Run performance/Locust scripts to verify speedup >= 80% and no connection leaks | 2 | IN_PROGRESS |
| 4 | Verification Suite | Verify all 626 pytest cases pass successfully | 3 | IN_PROGRESS |
| 5 | Completion | Produce handoff.md and notify parent orchestrator | 4 | PLANNED |

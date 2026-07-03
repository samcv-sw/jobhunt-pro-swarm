# Work Plan

This plan details the steps to fulfill the Backend Optimization scope.

## Steps

1. **Exploration**:
   - Spawn 3 Explorer agents in parallel to investigate the codebase.
   - Specifically investigate:
     - Celery integration in FastAPI and verify if there is any blocking event loop scenario (e.g., synchronous Celery `delay()` or wait calls running directly in async route handlers without running in threads or async queueing).
     - DB connection resilience in `backend/sync_worker.py` and where/how `asyncpg.PostgresConnectionError` could occur.
     - FastAPI routers in `backend/` and verify which endpoints are under `/api/v1/*` and their current security dependency setup.
     - Review test files: `tests/e2e/test_database.py`, `test_e2e_backend.py`, and `test_r4_auth.py` to understand E2E expectations.

2. **Implementation Planning**:
   - Collect and synthesize reports from the 3 Explorers.
   - Define exact code modifications to be performed by the Worker.

3. **Execution (Worker)**:
   - Spawn a Worker with a verification checklist.
   - Worker implements the required fixes and checks.
   - Worker runs tests/verifies builds.

4. **Review (2 Reviewers)**:
   - Spawn 2 Reviewer agents independently.
   - Verify correctness, security, logical consistency, and that logical CSS/typography rules are followed if applicable (though this is backend, we check formatting and Arabic support if any is in response data).

5. **Challenger (2 Challengers)**:
   - Spawn 2 Challengers to empirically stress test:
     - FastAPI and Celery blocking (measure event loop latency, verify under 50ms).
     - Database retry logic (simulate database drop and verify retries work).

6. **Audit (Forensic Auditor)**:
   - Spawn Forensic Auditor to verify no cheating, no hardcoding, proper code logic.

7. **Synthesize & Handoff**:
   - Collect all outcomes and construct the handoff document.

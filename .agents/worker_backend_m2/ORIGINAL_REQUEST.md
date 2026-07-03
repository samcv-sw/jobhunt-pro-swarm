# Original Request — Backend Concurrency Worker (Replacement)

## 2026-07-03T12:40:00Z

You are the Backend Concurrency Worker (Replacement) for Milestone 2.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_backend_m2

Your mission is to complete the backend refactoring to utilize asynchronous patterns (FastAPI) and ensure the Celery/Redis task queue is configured for high-throughput, non-blocking execution.

### Key Tasks:
1. **Refactor Celery Tasks Retry Backoff in `backend/tasks.py`**:
   - Ensure `scrape_jobs` has: `raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))`
   - Correct `generate_cover_letter`'s retry backoff: replace `countdown=10` with `countdown=10 * (2 ** self.request.retries)`
   - Implement manual retry with exponential backoff for `send_application_email`: replace the `autoretry_for` decorator approach with a manual try-except block in the task body that catches exception and raises: `self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))` up to `max_retries=5`.
2. **Review/Ensure non-blocking FastAPI handlers in `backend/main.py`**:
   - Verify endpoints like `/api/v1/scrape` and `/api/v1/generate-cover-letter` call `.delay(...)` using `asyncio.to_thread` or loop executor so uvicorn's event loop does not block.
3. **Verify production reliability Celery settings in `backend/celery_app.py`**:
   - Ensure the configuration includes: `task_acks_late=True`, `worker_prefetch_multiplier=1`, `broker_connection_retry_on_startup=True`.
4. **Run Concurrency and Backend Tests**:
   - Run `pytest tests/test_concurrency.py` and `pytest tests/test_backend.py`.
   - Document the test execution command and output results.

### MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When finished, write a detailed handoff.md in your working directory and notify the sub-orchestrator (Conv ID: 85146802-97a8-4bda-ba03-175341fb09cb) via a message. Do not write placeholder code.

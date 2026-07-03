# Scope: Backend Concurrency and Asynchronous Task Queue Optimization

## Architecture
- **API Boundary**: FastAPI endpoints in `backend/main.py` serve as the HTTP interface for job scraping, cover letter generation, and websocket war room.
- **Message Broker & Result Backend**: Redis broker routes tasks to specific queues (`scraping`, `ai_inference`, `email_sender`) defined in `backend/celery_app.py`.
- **Worker Execution**: Celery worker processes execute tasks in `backend/tasks.py` concurrently.
- **Concurrency Pattern**: FastAPI endpoint handlers must be fully asynchronous. Dispatches to Celery (e.g. `scrape_jobs.delay()`) use blocking network I/O which must be offloaded (e.g. `asyncio.to_thread` or `loop.run_in_executor`) to prevent uvicorn's event loop from stalling under high load.

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID |
|---|---|---|---|---|---|
| 1 | Exploration & Analysis | Inspect current FastAPI endpoints, Celery workers, and test infrastructure. Identify blocking bottlenecks. | None | DONE | 0d9029b1-86c1-470d-b54a-ad15d2f90306 |
| 2 | Asynchronous Refactoring | Modify `backend/main.py`, `backend/tasks.py`, and `backend/celery_app.py` to ensure fully async, non-blocking task enqueuing and configure Celery retry logic with backoff. | M1 | IN_PROGRESS | 59e7750d-0fea-461e-bef0-d285d4154b6f |
| 3 | Verification & Review | Review code correctness, thread safety, and verify non-blocking event loop execution under concurrency. | M2 | PLANNED | |
| 4 | Forensic Audit & Handoff | Run forensic audit checks, verify code integrity, synthesize findings, and write handoff report. | M3 | PLANNED | |

## Interface Contracts
### FastAPI Endpoints ↔ Celery Tasks
- `/api/v1/scrape` (POST):
  - Request: `ScrapeRequest(user_id: str, target_urls: list[str])`
  - Response: `{"status": "queued", "task_id": str}`
  - Non-blocking: Celery enqueue must not block FastAPI main event loop.
- `/api/v1/generate-cover-letter` (POST):
  - Request: `CoverLetterRequest(user_cv: str, job_description: str)`
  - Response: `{"status": "queued", "task_id": str}`
  - Non-blocking: Celery enqueue must not block FastAPI main event loop.

### Celery Task Retry Policy
- `scrape_jobs`: Retries up to 3 times, countdown: `60 * (2 ** self.request.retries)`.
- `generate_cover_letter`: Retries up to 3 times, countdown: `10 * (2 ** self.request.retries)`.
- `send_application_email`: Retries up to 5 times, countdown: `300 * (2 ** self.request.retries)`.

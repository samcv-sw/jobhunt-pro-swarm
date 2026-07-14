# Project: JobHunt Pro Optimization and Enhancements

## Architecture
- Backend: FastAPI application with SQLite database (models in `backend/models.py`, routers in `backend/main.py` and `web/routers/`).
- Frontend: Next.js App Router (in `frontend/src/`) using Tailwind CSS and translation widgets.
- Testing: Pytest test suite with 608 test cases (`tests/` folder).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Initial Investigation | Explore codebase for database bottlenecks, frontend structures, and test setup. | None | DONE |
| 2 | Backend Router Optimization | Refactor DLQ requeue, webhooks, query indices, and dashboard queries. | M1 | PLANNED |
| 3 | Frontend UI/UX Enhancement | Ensure logical properties, Cairo/RTL typography scaling, and proper language toggles. | M1 | PLANNED |
| 4 | verification | Execute all 608 pytest cases, verify OpenAPI Swagger, and run Forensic Auditor. | M2, M3 | PLANNED |

## Interface Contracts
- `/api/v1/admin/dlq/requeue`: POST endpoint returning `{"requeued": count, "cutoff_utc": timestamp}`.
- `/api/v1/webhooks/brevo`: POST endpoint accepting list of events and returning `{"status": "ok", "processed": count}`.
- `/api/v1/webhooks/sendgrid`: POST endpoint accepting list of events and returning `{"status": "ok", "processed": count}`.
- `/api/dashboard/stats`: GET endpoint returning combined metrics for user campaigns and wallet balance.

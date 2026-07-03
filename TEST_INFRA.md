# E2E Test Infrastructure — JobHunt Pro

This document describes the End-to-End (E2E) testing framework, testing philosophy, feature inventory, test architecture, and coverage thresholds for JobHunt Pro.

## 1. Testing Philosophy
Our E2E testing strategy focuses on validating the system's core capabilities across multiple tiers (Tiers 1-4) in a realistic environment. We prioritize:
- **Local-First Zero-Latency Verification**: Ensuring the SQLite database operates in WAL mode with Foreign Key constraints enabled, and that transactions are correctly captured in the Outbox model (`ps_crud_outbox`).
- **Asynchronous Flow Integrity**: Verifying that the backend event loop remains highly responsive (delay < 30ms) during Celery task creation, preventing event loop blocking.
- **RTL & Arabic Readability Compliance**: Validating font sizes, line heights, dynamic layouts, and contextual input direction (`dir="auto"`) to meet UX standards.
- **Reliable Data Sync**: Ensuring outbox logs are successfully streamed to the remote Postgres DB and updated to `synced = True` in SQLite, with proper handling of cold starts and connection errors.

## 2. Feature Inventory
The E2E tests cover the following features:
- **Database Local-First WAL Mode**: Confirms local SQLite runs in WAL mode and foreign keys are enforced.
- **Outbox CRUD Tracking**: Verifies INSERT, UPDATE, and DELETE operations correctly generate and log payloads into the outbox.
- **Sync Worker Pipeline**: Confirms records are queried, pushed to remote Postgres, and marked synced.
- **Event Loop Responsiveness**: Validates non-blocking dispatch of scrape and cover letter generation tasks.
- **Celery Task Routing**: Verifies tasks route to their designated queues (`scraping`, `ai_inference`, `email_sender`).
- **Celery Task Retries**: Validates exponential backoff and jitter retry configurations.
- **Endpoint Input Validation**: Confirms proper 422 HTTP validation responses on malformed input payloads.
- **Arabic Typography & Readability**: Enforces min font size >= 14px, line-height 1.6-2.0, and no letter-spacing for Arabic text.
- **RTL Forms & Icons**: Checks for input `dir="auto"` and scaleX dynamic mirroring for RTL layouts.

## 3. Test Architecture
The testing suite runs on `pytest` using the `pytest-asyncio` plugin for asynchronous database and endpoint operations.
- **Frontend Audits**: Code/style inspection tests in `tests/e2e/test_frontend.py`.
- **Backend Flow Verification**: API request and loop monitoring in `tests/e2e/test_backend.py`.
- **Database WAL & Sync Worker**: Local SQLite validation and mock cloud DB integration tests in `tests/e2e/test_database.py`.

## 4. Coverage Thresholds
We mandate:
- **E2E Test Coverage**: 100% of defined critical flows (Tiers 1-4).
- **Event Loop Delay Limit**: < 30ms max latency under concurrent task generation.
- **Arabic Typography rules**: Zero styling violations on Arabic/RTL classes.
- **Error Handling**: Graceful recovery and retry for database connection dropouts.

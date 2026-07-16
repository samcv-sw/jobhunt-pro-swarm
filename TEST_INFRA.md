# E2E Test Infrastructure — JobHunt Pro

This document describes the End-to-End (E2E) testing framework, testing philosophy, feature inventory, test architecture, and coverage thresholds for JobHunt Pro SaaS.

## 1. Testing Philosophy
Our testing strategy ensures maximum reliability, performance, and security of JobHunt Pro's core workflows by organizing tests across four distinct, progressive execution tiers. We focus on:
- **Local-First Reliability & Compatibility**: Ensuring SQLite operates correctly as a local fallback and translates queries transparently to PostgreSQL using the DB shim (`core/pg_sqlite_shim.py`), maintaining state integrity under connection dropouts.
- **Asynchronous Flow Integrity**: Verifying that backend operations (FastAPI app and Celery worker layer) route async tasks without blocking the web server's main event loop.
- **Arabic & RTL Readability Compliance**: Validating Arabic typography hierarchy (font-sizes >= 14px, line-height 1.6-2.0, no letter-spacing) and forms/inputs behavior (dynamic RTL mirroring, `dir="auto"`) across templates and Next.js frontend pages.
- **Adversarial & Security Hardening**: Validating access control, WAF rule matching, CORS origins, JWT rotation rules, rate limiters, and endpoint bypasses.

## 2. Feature Inventory
The test suite validates the following core features of the JobHunt Pro SaaS:
- **Local Database & Shim**: WAL-mode validation, foreign key constraints, connection checkout loop, connection recycling (280s age threshold), and pre-ping query (`SELECT 1`).
- **Sync Worker Pipeline**: Unsynced outbox tracking, remote Postgres push, reconnection stress under connection dropouts, and Celery task routing.
- **Stealth Scrapers & Reliability**: Stealth scrape flat maps, proxy verification, caching, and fallback execution between `nodriver`, `camoufox`, and default scrapers.
- **Security & Aegis/Banshield Hardening**: WAF hacker probe blocking, access control on sensitive system endpoints, CORS origin checks, JWT rotation, and daily token cap limits.
- **AI Engines & Resume/Cover Letter Generators**: Parsing job keywords, LLM providers pool fallback mechanisms, cover letter customization, and ATS matching scoring (including Arabic-specific matching).
- **Celery Tasks**: Asynchronous Celery task execution, non-blocking FastAPI loops, routing tasks to designated queues (`scraping`, `ai_inference`, `email_sender`), and exponential backoff configuration.
- **User Interface & RTL Layout**: Validation of Arabic fonts (`Cairo`, `Tajawal`), RTL page mirroring logic, and input-level directionality.

## 3. Test Architecture
The test suite runs on `pytest` using various plugins for async operations, property-based testing, and performance testing:
- **Test Runner Configuration (`pytest.ini`)**:
  ```ini
  [pytest]
  testpaths = tests
  norecursedirs = _backups .git .github scratch
  python_files = test_*.py
  pythonpath = .
  ```
- **Active Pytest Plugins**:
  - `anyio` and `asyncio`: Manage asynchronous testing hooks and fixture loop scopes.
  - `hypothesis`: Enables property-based/generative stress testing for edge cases.
  - `locust`: Supports load testing.
  - `Faker`: Generates mock profile data.
  - `logfire` & `langsmith`: Distributed tracing and LLM evaluation monitoring.
  - `mock`: Direct unit level patching.

## 4. Coverage Thresholds
We mandate the following operational and coverage rules:
- **Tiered Flow Coverage**: 100% pass rate across all 626 test cases covering Tiers 1 to 4.
- **Event Loop Responsiveness**: Less than 30ms latency under high task-dispatch rates.
- **Memory Allocation Limits**: Celery worker recycling (`worker_max_tasks_per_child=10`) and supervisor-enforced memory limits (Celery < 180MB, DB Sync < 80MB, Uvicorn < 220MB) to prevent container OOMs.
- **Arabic Typography Rules**: Zero violations of minimum font size (14px) and line height (1.6-2.0) guidelines on Arabic template tags.
- **Database Resilience**: Reconnection attempt intervals and dead-letter queue (DLQ) poison pill non-blocking behavior.

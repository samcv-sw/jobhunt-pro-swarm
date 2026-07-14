# Review & Adversarial Audit Report: Cloud Deployment & Stealth Reliability

**Date**: 2026-07-12
**Auditor**: teamwork_preview_reviewer_2 (Reviewer and Adversarial Critic)

---

# SECTION 1: Quality Review

## Review Summary

**Verdict**: REQUEST_CHANGES

The JobHunt Pro workspace implementation has been reviewed for correctness, completeness, robustness, and interface conformance. While the dynamic CORS middleware, keep-alive workflow, Celery memory guard supervisor, and connection string formatter are conceptually sound and pass all unit tests, **two critical deployment gaps** were discovered that prevent the Celery Memory Guard and PgBouncer connection reuse from functioning correctly in production.

Specifically:
1. **Missing Production Dependency**: `psutil` (which is required by the Memory Guard in `start_cloud.py`) is completely omitted from the root `requirements.txt` and `pyproject.toml`. In production, this causes the memory supervisor to skip all RAM usage tracking and OOM prevention recycles.
2. **Legacy DB Connection Pool Bypass**: The legacy connection layer in `core/pg_sqlite_shim.py` (which translates SQLite queries for PostgreSQL) does not call `format_neon_connection_string` and defaults to a threaded connection pool size of `PG_POOL_MIN=5` and `PG_POOL_MAX=80`. This bypasses PgBouncer parameters and easily exceeds the 10-connection limit on Neon's free tier.

---

## Findings

### [Major] Finding 1: Missing `psutil` Dependency in Requirements
- **What**: The memory monitor supervisor in `start_cloud.py` depends on the `psutil` library to inspect process RSS and recycle leaky Celery/Uvicorn processes. However, `psutil` is not declared in `requirements.txt` or `pyproject.toml`.
- **Where**: `requirements.txt`, `pyproject.toml`, and `start_cloud.py` (Line 214).
- **Why**: When the application is deployed to platforms like Render using the standard `requirements.txt` (as defined in `render.yaml`), `psutil` is not installed. The supervisor falls back to a warning log and disables all memory checks and process recycling, rendering the Celery Memory Guard useless.
- **Suggestion**: Add `psutil>=5.9.0` to the root `requirements.txt` and `pyproject.toml` dependencies.

### [Major] Finding 2: Legacy DB Connection Pool Exceeds Neon Free Tier Limits
- **What**: `core/pg_sqlite_shim.py` handles DB connection pooling for the legacy SaaS API (`web/app_v2.py`) and does not format the Neon URL. It sets a connection pool size of `min_conn=5` and `max_conn=80`.
- **Where**: `core/pg_sqlite_shim.py` (Lines 449-457) and `web/app_v2.py`.
- **Why**: While `backend/database.py` restricts its connection pool size to `pool_size=3` and `max_overflow=2` (max 5) to respect Neon's free tier limit of 10 concurrent connections, the legacy SQL shim can spawn up to 80 connections. If a few requests hit the legacy endpoints, the Neon connection limit will be instantly exhausted, throwing `OperationalError: too many connections`. Furthermore, since it does not format the URL using `format_neon_connection_string`, it bypasses the transaction pooler `-pooler` hostname and prepared statement disabling.
- **Suggestion**: Import `format_neon_connection_string` in `core/pg_sqlite_shim.py` to process `NEON_URI` and restrict the pool sizes (`min_conn=1`, `max_conn=3`) to ensure they stay within limits.

### [Minor] Finding 3: Redundant GitHub Keep-Alive Workflows
- **What**: The `.github/workflows/` directory contains three separate keep-alive workflow files doing nearly identical tasks: `keep-alive.yml`, `keep_alive.yml`, and `keepalive.yml`.
- **Where**: `.github/workflows/keep-alive.yml`, `.github/workflows/keep_alive.yml`, `.github/workflows/keepalive.yml`.
- **Why**: This creates duplicate GitHub Actions runs (every 10 or 12 minutes) and clutters the workflow history.
- **Suggestion**: Consolidate them into a single `keepalive.yml` that pings the Render backend `/healthz` endpoint and runs the database warmer.

### [Minor] Finding 4: Neon DB Warmer Fails Workflow on Missing Secret
- **What**: The new `core/neon_warmer.py` exits with status `1` if the database URL is not configured:
  ```python
  database_url = os.getenv("DATABASE_URL")
  if not database_url:
      logger.warning("DATABASE_URL not set — skipping Neon warm-up")
      return False
  ```
- **Where**: `core/neon_warmer.py` (Line 38).
- **Why**: For repositories where `DATABASE_URL` is not set (e.g. running on local SQLite dev only), the GitHub Actions cron job will run and fail every 12 minutes, generating spam notifications.
- **Suggestion**: Exit with status `0` if `DATABASE_URL` is empty, since skipping warm-up on local/SQLite-only setups is expected behavior and not a workflow failure.

---

## Verified Claims

- **Stealth Reliability Unit Tests** → Verified via `pytest tests/test_stealth_reliability.py` → **PASS** (All 3 tests passed successfully).
- **CORS Dynamic Validation Unit Tests** → Verified via `pytest tests/test_cors_validation.py` → **PASS** (All 20 tests passed successfully).
- **Cloud Optimization Unit Tests** → Verified via `pytest tests/test_cloud_optimizations.py` → **PASS** (All 2 tests passed successfully).
- **Keep-Alive Health Endpoint** → Verified via `pytest tests/test_keep_alive.py` → **PASS** (Pings `/api/v1/health` returning 200 OK).
- **Celery Integration and Routing Tests** → Verified via `pytest tests/test_celery_integration.py` → **PASS** (All 9 tests passed successfully).
- **Frontend Production Compilation** → Verified via `npm run build` in `/frontend` → **PASS** (Compiled Next.js static pages under `/`, `/_not-found`, and `/dashboard` successfully in 5.4s).
- **Python Source Files Compile Check** → Verified via `python -m py_compile` on modified source files → **PASS** (All files compiled successfully).

---

## Coverage Gaps

- **Integration Database Testing under PgBouncer** — Risk level: **MEDIUM**. The unit tests mock `format_neon_connection_string` but do not perform live integration tests of SQLAlchemy and `asyncpg` queries executing through a transaction pooler.
- **Docker Cloud Deployment Build** — Risk level: **HIGH**. `Dockerfile.cloud` copies `requirements-cloud.txt` which does not exist in the root directory (it exists only under `archive/requirements-cloud.txt`), meaning the Docker build will fail out of the box.

---

## Unverified Items

- **Actual Render live scaling** — Reason: Sandbox environment does not connect to external Render APIs or active cloud hosting.

---

# SECTION 2: Adversarial Challenge Report

## Challenge Summary

**Overall Risk Assessment**: MEDIUM

The implementation is robust against standard functional paths, but several structural vulnerabilities exist under high-load, resource-constrained, or misconfigured environments. Specifically, the synchronous blocking nature of the proxy pool validator and the OOM supervisor loop recycling logic present potential deadlocks and service degradation issues.

---

## Challenges

### [High] Challenge 1: Synchronous Blocking Validation in Proxy Manager
- **Assumption Challenged**: Rotated proxy validation is fast enough to perform inline during scraping requests.
- **Attack Scenario**: When a large number of free proxies (e.g. 100) become stale or blocked (which is the typical state of public proxy lists after a few hours), `get_proxy()` shuffles and validates candidates sequentially. With a `timeout=3` seconds per proxy, validating a list of dead proxies will block the synchronous caller thread for up to **5 minutes** (100 * 3s).
- **Blast Radius**: The Celery worker or Sync Worker thread will completely freeze, blocking all subsequent job scraping and outbox synchronization tasks.
- **Mitigation**: Limit the candidate verification search to a maximum of 3–5 random proxies per invocation, or implement a background task that asynchronously warms and prunes the proxy pool.

### [Medium] Challenge 2: Supervisor OOM Recycling Loop
- **Assumption Challenged**: Process recycling will always recover the container footprint under 450MB.
- **Attack Scenario**: If the parent supervisor process itself develops a memory leak or grows in size, the global footprint `total_rss` (which includes the supervisor's RSS) will exceed 450MB. The supervisor will identify the largest child worker (e.g., Uvicorn or Celery) and recycle it. Once the child restarts, the global RSS will immediately exceed 450MB again because the supervisor remains bloated. The supervisor will enter an infinite loop of killing and restarting the child workers.
- **Blast Radius**: Persistent downtime for Uvicorn and Celery services while the container is stuck in a recycle loop.
- **Mitigation**: Exclude the supervisor's own RSS when determining which child process to recycle, or implement a maximum recycle rate limit (with container exit if the supervisor itself is bloated).

### [Medium] Challenge 3: Insecure Wildcard TLD CORS Patterns
- **Assumption Challenged**: Allowed CORS origins only contain trusted domains.
- **Attack Scenario**: The regex builder `_build_origin_regex(pattern)` parses wildcard subdomains but does not validate domain depth or check against a public suffix list. If a user sets `ALLOWED_ORIGINS` to `https://*.com` or `https://*.dev`, the regex `^https?://\*\.[a-zA-Z0-9-]+$` allows *any* `.com` or `.dev` domain.
- **Blast Radius**: Any website on the web can perform cross-origin requests to the API with credentials enabled, leading to CSRF-like data exposure.
- **Mitigation**: Restrict wildcard patterns to require at least two literal domain labels (e.g., `*.domain.tld`) and reject patterns like `*.com`.

### [Low] Challenge 4: Supervisor Process Fast Crash Loop
- **Assumption Challenged**: Services will not fail immediately upon restart.
- **Attack Scenario**: If Uvicorn or Celery fails immediately on startup (e.g., due to a syntax error or a database migration failure), the supervisor loop restarts them immediately on the next 5-second tick.
- **Blast Radius**: High CPU utilization and log floods from rapid process respawning.
- **Mitigation**: Implement an exponential backoff delay before restarting processes that exited quickly.

---

## Stress Test Results

- **CORS Attacker Domain Subdomain Hijack** → Rejected wildcard match → `https://attacker-jobhunt-pro.com` correctly denied access → **PASS**
- **CORS TLD Injection Attack** → Rejected suffix match → `https://jobhunt-pro.com.evil.com` correctly denied access → **PASS**
- **CORS Localhost Custom Port Bypass** → Port mismatches rejected → `https://jobhunt-pro.com:8443` correctly denied access → **PASS**
- **Neon connection port overrides** → Handled correctly in connection string string modifications → **PASS**

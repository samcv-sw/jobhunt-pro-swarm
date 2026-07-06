# Handoff Report: DB Sync & Production Security Audit

## 1. Observation

Direct observations from the codebase files and execution of the test suites:

### A. Database Synchronization (SQLite <-> Neon PostgreSQL)
- **Local outbox recording**: In `backend/main.py` lines 123-136, local mutations and their corresponding outbox logs are written atomically in the same local transaction:
  ```python
  async with async_session() as session:
      account = Account(tenant_id=req.tenant_id, ...)
      session.add(account)
      await session.flush()
      
      outbox = SyncOutbox(table_name="accounts", record_id=str(account.id), operation="INSERT", payload={...}, synced=False)
      session.add(outbox)
      await session.commit()
  ```
- **Sync worker loop & reconnection**: In `backend/sync_worker.py` lines 73-85, the sync worker runs an infinite loop that reconnects to Neon PostgreSQL on each cycle:
  ```python
  while True:
      cloud_conn = None
      try:
          raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://")
          ...
          cloud_conn = await asyncpg.connect(raw_pg_url)
  ```
- **Batch processing & exception handling**: In `backend/sync_worker.py` lines 100-125, the worker commits successful records, breaks the batch on connection drop, and catches exceptions to sleep for 30 seconds:
  ```python
  for record in unsynced_records:
      try:
          success = await _push_record_to_cloud(cloud_conn, record)
          if success:
              record.synced = True
              synced_count += 1
          ...
      except CONNECTION_EXCEPTIONS as e:
          connection_error = e
          break
  await session.commit()
  if connection_error:
      raise connection_error
  ...
  except (asyncpg.Error, asyncpg.InterfaceError, OSError, asyncio.TimeoutError) as e:
      logger.warning(f"[SyncWorker] Remote DB connection lost/unreachable (will retry in 30s): {e}")
  ```
- **Idempotent inserts (Duplicate protection)**: In `backend/sync_worker.py` lines 33-38, the insert uses `ON CONFLICT DO NOTHING`:
  ```sql
  INSERT INTO sync_outbox_log (table_name, record_id, operation, payload, created_at)
  VALUES ($1, $2, $3, $4::jsonb, $5)
  ON CONFLICT DO NOTHING
  ```
  The table schema defined in `explorer_k8s_2/analysis.md` line 315 shows a matching unique constraint:
  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_outbox_log_uniq ON sync_outbox_log(table_name, record_id, created_at);
  ```
- **Soft Errors & Dead-Letter Queue (DLQ)**: In `backend/sync_worker.py` lines 49-62, data formatting or serialization errors are written to `backend/dead_letter_queue.log` and returned as `False` (marking them as synced to prevent blocking the worker):
  ```python
  except Exception as e:
      logger.error(f"Failed to push record {record.id} to cloud (soft error/data failure): {e}")
      # writes record and exception details to dead_letter_queue.log
      return False
  ```
- **PostgreSQL Latency Measurement**: No execution time recording (`time.perf_counter()`), query logging, telemetry, or profiling logic is implemented in `backend/sync_worker.py` or `backend/database.py`. The web application's database factory `get_db()` in `web/shared.py` configures connection pooling using SQLAlchemy's `QueuePool` with parameters (`pool_pre_ping=True`, `pool_recycle=280`, and timeouts), but does not record query execution time.

### B. Production Security (JWT, Rate Limiting, Cookie/Session Protection)
- **JWT Verification**: Endpoint authentication is applied via FastAPI dependencies (`verify_jwt`) in `backend/main.py` (e.g. `trigger_scrape` at line 86, `trigger_cover_letter` at line 94, `stream_cover_letter` at line 99, `create_account` at line 109) and `web/routers/billing.py` (e.g. `create_checkout_session` at line 16).
- **WebSocket Verification Claims Defect**: In `backend/main.py` lines 170-176, the WebSocket endpoint decodes the token but discards the payload and performs no database or user verification checks:
  ```python
  try:
      jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
  except Exception:
      await websocket.close(code=4001)
      return
  ```
- **JWT Hardcoded Fallback Vulnerability**: In `web/app_v2.py` lines 73-78, if the environment variable `JWT_SECRET_KEY` is missing, the web app defaults to a hardcoded key in production:
  ```python
  JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
  if not JWT_SECRET_KEY:
      if os.getenv("TESTING") == "true" or "pytest" in sys.modules or "unittest" in sys.modules:
          JWT_SECRET_KEY = "jobhunt-pro-secret-key-32bytes-ok!!"
      else:
          JWT_SECRET_KEY = "jobhunt-pro-secret-key-32bytes-ok!!"  # Hardcoded fallback!
  ```
  Conversely, `backend/auth.py` line 15 raises a `ValueError` if the key is missing in production.
- **Backend API Rate Limiter**:
  - In `backend/main.py` lines 19-37, the rate limiter uses a process-local in-memory sliding window using `defaultdict(list)` with a global `asyncio.Lock()` to serialize checks.
  - Client identification: It uses `request.client.host` directly (lines 27-33):
    ```python
    client_ip = request.client.host if request.client else "unknown"
    ```
  - Endpoints lacking rate limiting: The limiter is omitted from `create_account` (`/api/v1/accounts`) and `create_checkout_session` (`/api/v1/checkout`).
- **SaaS Web Rate Limiter**:
  - In `web/shared.py` lines 176-210, `_check_rate_limit` stores rate-limiting counters in the database.
  - transient key mapping: The database key includes `id(store)` (lines 185):
    ```python
    db_key = f"rl:{id(store)}:{ip}"
    ```
  - Fixed Window logic: The rate limiter checks if `now - db_time > window_seconds` before resetting, implementing a fixed window instead of a sliding window.
- **Session/Cookie Protection**:
  - No session or cookie tables exist in `init.sql` or `backend/models.py`. All sessions are stateless and cookie-based.
  - Starlette `SessionMiddleware` is configured with `https_only=True` (setting the `Secure` flag) and `same_site="lax"`.
  - The custom `user_id` cookie set in `web/routers/auth.py` lines 172 and 195, and `web/app_v2.py` line 9852, does **not** specify `secure=True`, which allows it to transmit over unencrypted HTTP:
    ```python
    resp.set_cookie("user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax")
    ```
  - plaintext API Keys: In `web/routers/auth.py` line 105, user API keys are generated via `secrets.token_urlsafe(32)` and stored directly in the database (`users.api_key` column) in plaintext.

---

## 2. Logic Chain

1. **DB Sync Robustness**:
   - Because mutations are recorded in the local outbox (`ps_crud_outbox`) and the background worker only marks them as synced after obtaining a successful response from Postgres, a connection loss cannot cause data loss (unsynced items are retried).
   - Because the worker commits the local database session outside the record loop, successfully processed items are committed even if the loop breaks mid-batch due to a connection drop (preventing unnecessary replication of succeeded items).
   - Because the remote query uses `ON CONFLICT DO NOTHING` matching the unique index `idx_sync_outbox_log_uniq`, the system is resilient against duplicate inserts if the local transaction fails to commit after a successful remote write.
   - Because soft errors are routed to `dead_letter_queue.log` and returned as `False`, corrupt or invalid payloads are quarantined without halting the background syncer or causing infinite loop blockages.

2. **Telemetry Gaps**:
   - Because there is no time measurement, telemetry logging, or metric instrumentation around the `asyncpg` execution in `sync_worker.py`, it is impossible to detect slow Neon queries, connection pool exhaustion, or service degradation before errors or timeouts occur.

3. **WebSocket Vulnerability**:
   - Because the WebSocket authentication routine decodes the token using `jwt.decode` but discards the payload without inspecting claims (like `sub`) or looking up the user in the database, a connection will be successfully established for *any* signature-valid token. An attacker can forge a token with an empty payload `{}` or use an expired/revoked user's token and still establish a WebSocket session.

4. **Hardcoded Secret Vulnerability**:
   - Because `web/app_v2.py` falls back to `"jobhunt-pro-secret-key-32bytes-ok!!"` if the `JWT_SECRET_KEY` environment variable is missing, any deployment that omits this variable will automatically run with a public key, allowing malicious actors to forge valid JWT tokens.

5. **Rate Limiting Flaws**:
   - Because the backend rate limiter relies on `request.client.host`, it is proxy-unaware. When deployed behind a reverse proxy (e.g., Nginx, Cloudflare), all clients appear as the proxy IP, creating a global denial-of-service vulnerability (where one busy client triggers a rate limit block for all users).
   - Because client IP keys are never removed from the backend `self.history` dictionary, a slow memory leak will occur in long-running processes as unique IPs visit the API.
   - Because `_check_rate_limit` in the web router uses `id(store)` (which is transient and unique per process memory space), multiple worker processes (e.g. Uvicorn worker replicas) will write to different keys (`rl:{id(store)}:{ip}`) in the shared Neon database, breaking rate limit synchronization.

6. **Cookie & Plaintext Key Protection**:
   - Because the custom `user_id` cookie lacks `secure=True`, browsers will send it over plain HTTP, exposing it to packet sniffing.
   - Because user API keys are stored in the database in plaintext without hashing, a database leak immediately compromises all API keys.

---

## 3. Caveats

- **No Live Production Traffic Investigation**: This audit was completed entirely via code inspection and local test executions. Behavior under massive real-world traffic was not monitored directly.
- **Proxy Configuration Assumptions**: We assumed a standard reverse-proxy setup (e.g., Nginx, Cloudflare) is used for production deployment, which exposes the proxy-unaware IP mapping flaw. If the application is accessed directly, this specific proxy-unaware flaw is mitigated, but the memory leak and global lock contention remain.

---

## 4. Conclusion

1. **Database Sync**: The outbox-based synchronization protocol is highly resilient to connection drops, network flapping, and poisoned payloads. Data loss is successfully avoided, and duplicates are handled correctly. However, a major telemetry gap exists; there is no profiling or latency logging for remote PostgreSQL queries.
2. **JWT Authentication**: JWT authentication is structurally active on all API endpoints. However, a critical key-check fallback in `web/app_v2.py` compromises security if environment variables are missing. Additionally, WebSocket authentication is incomplete, verifying only the signature and discarding claims.
3. **Rate Limiting**: The custom backend rate limiter is highly fragile, suffering from proxy-IP spoofing/DoS vulnerabilities, memory leaks, and global request serialization bottlenecks. The web rate limiter fails database synchronization across multiple worker processes due to using transient dictionary IDs in its database keys.
4. **Sessions/Cookies**: HTTP sessions are appropriately stateless, but the primary authentication cookie (`user_id`) is insecure because it lacks the `secure=True` attribute. The storage of long-lived API keys in plaintext in the database is a significant security risk.

---

## 5. Verification Method

To independently verify these findings, run the following test commands from the project root:

### A. Connection Flapping and DLQ Poison Pill Resilience
Run the sync worker stress tests:
```powershell
pytest tests/test_sync_reconnection_stress.py tests/test_sync_dlq_poison_pill_stress.py
```
*Expected Result*: Tests pass, verifying that the worker recovers from network drops without losing data, and poison pills are safely logged to `dead_letter_queue.log` and skipped.

### B. Security Flaws (Rate Limiting, WebSocket claims bypass, JWT fallback, SSL Cookies)
Run the adversarial security test suite:
```powershell
pytest tests/test_adversarial_security.py
```
*Expected Result*: Tests pass, confirming that:
- Proxy-unaware rate-limiting triggers 429 globally when requests with different `X-Forwarded-For` headers are sent.
- WebSockets accept tokens with empty claims payloads.
- All v1 endpoints require valid JWT authentication.

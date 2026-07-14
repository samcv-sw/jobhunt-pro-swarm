# Handoff Report: Milestone 3 - DB and Cache Rate-Limit Shield

## 1. Observation

During my investigation of the codebase, I observed the following implementation details:

### Cache & Redis Usage
1. **Upstash Redis Caching via REST API**:
   - In `core/edge_cache.py`, the `EdgeCache` class executes Redis commands over HTTP REST using `httpx.AsyncClient` to avoid connection limits and scaling bottlenecks.
   - Deterministic LLM cache key generation and caching helpers are defined on lines 90-141:
     - `_make_llm_cache_key(job_description: str, user_cv: str) -> str`
     - `cache_llm_result(...)` and `get_cached_llm_result(...)`
   - In `backend/ai_engine.py`, the cover letter generation logic calls the edge cache to read and write cover letters (lines 48, 96, 126, 187).
   - In `core/ats_matcher.py`, the `analyze_with_groq_async` function uses `edge_cache` to cache ATS calculations (lines 1167, 1210, 1243).
   - In `core/multi_tenant.py`, `edge_cache` is used to store and retrieve active campaign data (`"hydra_active_campaigns"`) with a TTL of 120 seconds (lines 399, 414).

2. **Standard Sockets Redis Caching (fastapi-cache)**:
   - In `backend/cache.py`, the setup code imports `fastapi_cache` (lines 31-42) and configures standard Redis sockets with a connection pool capped at `max_connections=10` to respect the Upstash free-tier socket limit.

3. **Direct Sockets Redis Caching (ATS Matcher)**:
   - In `core/ats_matcher.py` (lines 1296-1311 and 1342-1348), the function `full_ats_analysis` connects directly to Redis using the `redis` package over standard sockets via `os.environ.get("REDIS_URL")`. It performs `_redis_client.get(cache_key)` and `_redis_client.setex(cache_key, 86400, json.dumps(result))`.

4. **API Rate Limiting Middleware**:
   - In `web/app_v2.py` (lines 727-747), an ASGI middleware `_EdgeCacheRateLimitMiddleware` intercepts every incoming request (excluding `/ping`) and increments a client IP-based key (`rate_limit:{ip}`) on the shared `edge_cache` (Redis REST) using:
     ```python
     739:         count = await edge_cache.incr(key)
     740:         if count == 1:
     741:             await edge_cache.expire(key, 60)
     ```

---

### PostgreSQL / Neon Connection Pooling
1. **psycopg2 Threaded Connection Pool**:
   - In `core/pg_sqlite_shim.py` (lines 497-523), a global psycopg2 `ThreadedConnectionPool` is initialized:
     ```python
     508:                         min_conn = int(os.getenv("PG_POOL_MIN", "1"))
     509:                         max_conn = int(os.getenv("PG_POOL_MAX", "3"))
     510:                         # Ensure values are strictly bounded to (1, 3)
     511:                         min_conn = max(1, min(min_conn, 2))
     512:                         max_conn = max(min_conn, min(max_conn, 3))
     513: 
     514:                         cleaned_uri = clean_psycopg2_uri(NEON_URI)
     515:                         PG_POOL = pool.ThreadedConnectionPool(
     516:                             min_conn,
     517:                             max_conn,
     518:                             cleaned_uri,
     519:                             cursor_factory=DictCursor,
     520:                             connect_timeout=15,
     521:                         )
     ```
   - Connection recycling is implemented on lines 530-543, discarding connections older than 280 seconds to avoid silent timeouts.
   - Connection pre-pinging is implemented on lines 545-555 by running a lightweight test query (`"SELECT 1"`).
   - PID safety is enforced on lines 496-505, closing the pool and creating a new one if a child process fork is detected.

2. **Inactive SQLAlchemy Engine Pool**:
   - In `web/shared.py` (lines 87-105), a SQLAlchemy engine `_pg_engine` is built with a `QueuePool` size of 3 and `max_overflow=7`.
   - However, the function returns `shim.connect(db_url)` (line 105), which bypasses `_pg_engine` completely and uses the psycopg2 pool from `core/pg_sqlite_shim.py`. Consequently, the SQLAlchemy pool configuration is entirely inactive.

---

### Database Wakeup and Fallback Configuration
1. **SQLite Immediate Fallback**:
   - In `core/pg_sqlite_shim.py` (lines 836-843), `connect()` attempts to return a `PgConnectionWrapper()`. If that fails, it immediately catches the exception and returns a `SqliteConnectionWrapper(target_db)` (SQLite).
   - If Neon is sleeping (cold start), the `pool.ThreadedConnectionPool` constructor fails immediately on the first connection attempt. Because there is no retry loop around the pool creation, the system immediately drops PostgreSQL and shifts to SQLite.
   - This causes a "split-brain" state: writes are committed locally to SQLite while Neon is waking up, but subsequent requests after Neon is online write directly to Postgres, resulting in data desynchronization.

---

## 2. Logic Chain

1. **Redis Rate-Limit Shielding**:
   - **Premise**: Upstash Redis free tier allows up to 10k commands per day.
   - **Observation**: The `_EdgeCacheRateLimitMiddleware` calls `edge_cache.incr` and `edge_cache.expire` over the REST API for every single incoming HTTP request.
   - **Deduction**: If the application receives 5,000 page views a day, the rate limiter alone consumes 5,000 `INCR` commands and 5,000 `EXPIRE` commands, completely exhausting the 10k daily limit.
   - **Conclusion**: We must intercept these rate-limiting keys locally in a thread-safe memory cache and bypass Upstash Redis entirely for rate limiting. Additionally, caching cover letters and ATS calculation keys in a thread-safe local cache with a size limit (to prevent memory leaks) will drastically shield Redis from redundant reads for identical inputs.

2. **Neon Connection Pooling**:
   - **Observation**: The SQLAlchemy `QueuePool` setup in `web/shared.py` is dead code because the function returns the psycopg2 connection from the shim.
   - **Deduction**: The actual connection pooling is governed by psycopg2's `ThreadedConnectionPool` in `core/pg_sqlite_shim.py` (capped at max 3 connections per process).
   - **Conclusion**: The dead SQLAlchemy engine code in `web/shared.py` should be cleaned up. The psycopg2 connection pool in the shim is already configured correctly with pre-ping, PID checks, and 280-second idle recycling, which is highly suited for Neon serverless database limits.

3. **Database Wakeup and Split-Brain Prevention**:
   - **Observation**: Neon Postgres auto-suspends after 5-10 minutes of inactivity and takes 3-10 seconds to wake up.
   - **Observation**: `pg_sqlite_shim.py` lacks retries for the connection pool initialization, falling fallback to SQLite immediately when Neon is asleep.
   - **Deduction**: Immediate fallback to SQLite on cold starts causes split-brain data states since writes are written to SQLite but never synced back to Postgres once it wakes up.
   - **Conclusion**: We must split the database fail-safety fallback into two stages:
     1. **Cold-Start Retry Loop**: Wrap `ThreadedConnectionPool` creation in a retry loop (e.g., 5 attempts, sleeping 3 seconds between attempts) to wait for Neon to wake up before falling back.
     2. **SQLite Write-Ahead Queue**: If Neon is truly offline after retries, return a SQLite connection flagged as `is_fallback`. Intercept all write queries (`INSERT`/`UPDATE`/`DELETE`), store them in a local SQLite table `pending_db_writes` as a queue, and execute them locally. Run a background task to replay these queries atomically on Postgres once it is back online.

---

## 3. Caveats

1. **Local Rate Limiting Scope**: Purely local in-memory rate limiting operates per worker process. If multiple worker processes are running behind a load balancer, the effective rate limit will be higher (e.g., 100 requests per process instead of 100 requests globally). For this application's traffic and free-tier scale, this is an acceptable trade-off to protect the 10k command limit.
2. **Replay Conflicts**: The Write-Ahead Queue assumes that conflicts (like auto-increment ID collisions) are minimized because Postgres uses `lastval()` or sequence-based IDs synced with the SQLite database schema. A schema discrepancy could stall the replay queue, requiring a dead-letter queue table for failed sync tasks.

---

## 4. Conclusion

To successfully implement Milestone 3, we recommend the following code modifications:

### Step 1: Implement Thread-Safe Local Caching in `core/edge_cache.py`
Add a thread-safe `ThreadSafeMemoryCache` inside `core/edge_cache.py`. Intercept all `get`, `set`, `incr`, and `expire` methods to serve rate-limiting keys locally and cache LLM/ATS results.

```python
# Proposed addition to core/edge_cache.py

import time
import threading
from collections import OrderedDict

class ThreadSafeMemoryCache:
    """Thread-safe LRU in-memory cache with TTL."""
    def __init__(self, max_size: int = 1000):
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size

    def get(self, key: str) -> object:
        with self._lock:
            if key not in self._cache:
                return None
            val, expires_at = self._cache[key]
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return val

    def set(self, key: str, value: object, ttl: int = None) -> None:
        expires_at = time.time() + ttl if ttl is not None else None
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                self._cache.popitem(last=False) # Evict LRU
            self._cache[key] = (value, expires_at)

    def incr(self, key: str, ttl: int = 60) -> int:
        with self._lock:
            if key in self._cache:
                val, expires_at = self._cache[key]
                if expires_at is None or expires_at > time.time():
                    new_val = int(val) + 1
                    self._cache[key] = (new_val, expires_at)
                    self._cache.move_to_end(key)
                    return new_val
                else:
                    del self._cache[key]
            
            # Cache miss or expired
            new_val = 1
            expires_at = time.time() + ttl
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (new_val, expires_at)
            return new_val

# Instantiate a global instance in core/edge_cache.py
local_memory_cache = ThreadSafeMemoryCache(max_size=1000)
```

Modify the methods of the `EdgeCache` class in `core/edge_cache.py` as follows:
```python
    async def get(self, key: str) -> object:
        # 1. Probe local memory cache first
        local_val = local_memory_cache.get(key)
        if local_val is not None:
            return local_val
            
        # 2. Check remote cache
        remote_val = await self._execute("GET", key)
        if remote_val is not None:
            # Cache remote hits locally for a default 5 minutes to shield subsequent commands
            local_memory_cache.set(key, remote_val, ttl=300)
        return remote_val

    async def set(self, key: str, value: str, ex: int = None) -> object:
        # 1. Update remote cache
        res = await self._execute("SET", key, value, "EX", ex) if ex else await self._execute("SET", key, value)
        # 2. Update local memory cache
        local_memory_cache.set(key, value, ttl=ex)
        return res

    async def incr(self, key: str) -> object:
        # If rate limit key, bypass Upstash Redis REST calls completely
        if key.startswith("rate_limit:"):
            return local_memory_cache.incr(key, ttl=60)
        return await self._execute("INCR", key)

    async def expire(self, key: str, seconds: int) -> object:
        if key.startswith("rate_limit:"):
            # Expiry is already managed locally on incr()
            return 1
        return await self._execute("EXPIRE", key, seconds)
```

---

### Step 2: Implement Thread-Safe Local Caching in `core/ats_matcher.py`
Add `local_memory_cache` protection to `full_ats_analysis` in `core/ats_matcher.py` to prevent direct Redis hits for identical CV + Job Description inputs.

---

### Step 3: Clean up SQLAlchemy Pool and Neon Pool Retries
In `web/shared.py`, remove the dead SQLAlchemy engine `_pg_engine` building code. 

In `core/pg_sqlite_shim.py`, wrap the connection pool creation in a retry loop to tolerate Neon cold start delays:

```python
# In PgConnectionWrapper.__init__ (core/pg_sqlite_shim.py)
                if PG_POOL is None:
                    POOL_PID = current_pid
                    max_pool_retries = 5
                    for pool_attempt in range(max_pool_retries):
                        try:
                            # Restrict connection limits to prevent exceeding Neon's limit
                            min_conn = int(os.getenv("PG_POOL_MIN", "1"))
                            max_conn = int(os.getenv("PG_POOL_MAX", "3"))
                            min_conn = max(1, min(min_conn, 2))
                            max_conn = max(min_conn, min(max_conn, 3))

                            cleaned_uri = clean_psycopg2_uri(NEON_URI)
                            PG_POOL = pool.ThreadedConnectionPool(
                                min_conn,
                                max_conn,
                                cleaned_uri,
                                cursor_factory=DictCursor,
                                connect_timeout=15,
                            )
                            logger.info("[DB] ThreadedConnectionPool created successfully.")
                            break
                        except psycopg2.OperationalError as pool_err:
                            if pool_attempt < max_pool_retries - 1:
                                logger.warning(
                                    f"[DB] Neon pool creation failed (cold start?): {pool_err}. "
                                    f"Retrying in 3 seconds... (Attempt {pool_attempt+1}/{max_pool_retries})"
                                )
                                time.sleep(3)
                            else:
                                raise pool_err
```

---

### Step 4: Implement SQLite Write-Ahead Log (WAL) Query Queue
Implement a write queue inside `SqliteConnectionWrapper.execute` when in `is_fallback` mode, storing writes locally in `pending_db_writes` while executing them locally to keep the active session consistent. 

Add a background worker function/task (e.g., Celery task) to synchronize writes back to Postgres in a single atomic transaction when it wakes up:

```python
async def sync_sqlite_to_postgres():
    """Background synchronizer replaying pending SQLite queries to Neon Postgres."""
    import sqlite3
    db_path = "jobhunt_saas_v2.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Ensure query queue table exists
            conn.execute(
                "CREATE TABLE IF NOT EXISTS pending_db_writes ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "sql_query TEXT NOT NULL, "
                "query_params TEXT NOT NULL, "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            rows = conn.execute(
                "SELECT id, sql_query, query_params FROM pending_db_writes ORDER BY id ASC"
            ).fetchall()
    except Exception as e:
        logger.error(f"[Sync] Failed to read pending queries: {e}")
        return
        
    if not rows:
        return
        
    try:
        pg_conn = PgConnectionWrapper()
    except Exception as e:
        logger.warning(f"[Sync] Neon Postgres is offline: {e}. Retry scheduled.")
        return
        
    success_ids = []
    try:
        with pg_conn as active_pg:
            active_pg.execute("BEGIN")
            for row_id, sql_query, params_json in rows:
                params = json.loads(params_json)
                active_pg.execute(sql_query, params)
                success_ids.append(row_id)
            active_pg.commit()
    except Exception as tx_err:
        logger.error(f"[Sync] Transaction rolled back. Sync aborted: {tx_err}")
        return
        
    if success_ids:
        try:
            with sqlite3.connect(db_path) as conn:
                placeholders = ",".join("?" for _ in success_ids)
                conn.execute(f"DELETE FROM pending_db_writes WHERE id IN ({placeholders})", success_ids)
                conn.commit()
            logger.info(f"[Sync] Synced {len(success_ids)} queries successfully.")
        except Exception as del_err:
            logger.error(f"[Sync] Cleanup failed: {del_err}")
```

---

## 5. Verification Method

To verify these changes independently:

1. **Verify Caching Behavior**:
   - Run the unit tests suite:
     `pytest tests/test_hardening_v2.py`
     `pytest tests/test_llm_provider_pool.py`
   - Observe that mocking behavior remains intact. To verify local rate limits, run FastAPI in a local environment, invoke a route multiple times, and check console logs to ensure `[Upstash Redis]` REST endpoints are not called for rate limiting keys.

2. **Verify Neon Database Cold-Start Handling**:
   - Manually trigger a Neon sleep state (suspend compute node in the Neon dashboard).
   - Initiate a DB call from the web client.
   - Verify in console output that the log `"Neon pool creation failed (cold start?)"` occurs, retries are executed, and Neon eventually wakes up without triggering SQLite fallback.

3. **Verify SQLite WAL Queue Sync**:
   - Disconnect the internet or temporarily block PostgreSQL connection (e.g., invalidating `NEON_URL`).
   - Trigger a database write action. Confirm it executes locally on SQLite and adds a record in the SQLite `pending_db_writes` table.
   - Restore the PostgreSQL connection. Run the sync command/Celery task and verify the record is deleted from SQLite and appears inside Neon Postgres.

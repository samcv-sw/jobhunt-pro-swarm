# Handoff Report: Milestone 3 — DB and Cache Rate-Limit Shield

This report contains direct observations of the current database and cache configurations, a logical deduction chain, and detailed architectural proposals for implementing Milestone 3.

---

## 1. Observation

The codebase contains two key backend resource types: **Redis (Upstash)** and **PostgreSQL (Neon)**. The following details their current configurations and files of usage.

### Redis (Upstash) Caching Reference Locations
Redis is used for caching and rate-limiting in four distinct ways in the codebase:

1. **FastAPI Route Caching (`backend/cache.py`)**:
   - Uses `fastapi_cache` with a `RedisBackend` backed by `redis.asyncio` (`aioredis`).
   - Capped at 10 concurrent connections to respect Upstash's free-tier limits:
     ```python
     # backend/cache.py, lines 36-40
     pool = aioredis.ConnectionPool.from_url(
         redis_url,
         max_connections=10,   # Respect Upstash free-tier limit
         decode_responses=True,
     )
     ```
   - Falls back to `InMemoryBackend` if `REDIS_URL` is unset.
   
2. **Upstash HTTP REST Client (`core/edge_cache.py`)**:
   - Connects to Upstash Redis using the HTTP/REST API to bypass socket connection limits.
   - Credentials configured via `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`:
     ```python
     # core/edge_cache.py, lines 17-19
     self.url = os.environ.get("UPSTASH_REDIS_REST_URL")
     self.token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
     self.enabled = bool(self.url and self.token)
     ```
   - Implements cover letter caching using MD5/SHA256 hashed keys based on job descriptions and CVs:
     ```python
     # core/edge_cache.py, lines 104-115
     async def cache_llm_result(job_description: str, user_cv: str, result: dict, ttl: int = 3600) -> None:
         key = _make_llm_cache_key(job_description, user_cv)
         try:
             await edge_cache.set(key, _json.dumps(result), ex=ttl)
     ```

3. **Rate-Limiting Middleware (`web/app_v2.py`)**:
   - Every single HTTP request (excluding `/ping`) increments a rate-limit key in Upstash Redis via `edge_cache.incr` and sets an expiry via `edge_cache.expire`:
     ```python
     # web/app_v2.py, lines 727-747
     class _EdgeCacheRateLimitMiddleware:
         """Pure ASGI: edge cache + IP rate limit."""
         def __init__(self, app): self.app = app
         async def __call__(self, scope, receive, send):
             ...
             key = f"rate_limit:{ip}"
             count = await edge_cache.incr(key)
             if count == 1:
                 await edge_cache.expire(key, 60)
             if count and count > 100:
                 ...
     ```
   - This executes **1 to 2 Redis commands per HTTP request** whenever `edge_cache.enabled` is True.

4. **Synchronous Redis Driver (`core/ats_matcher.py`)**:
   - The function `full_ats_analysis` connects directly and synchronously to Upstash Redis:
     ```python
     # core/ats_matcher.py, lines 1298-1306
     _redis_url = os.environ.get("REDIS_URL")
     if _redis_url:
         try:
             import redis
             _redis_client = redis.from_url(_redis_url, socket_connect_timeout=2, socket_timeout=2)
             cached_raw = _redis_client.get(cache_key)
     ```
   - Caches ATS calculations using key `ats:<sha>` for a 24-hour TTL.
   - Also, `analyze_with_groq_async` uses `edge_cache` asynchronously to store intermediate AI analysis results using key `ats_match:<sha>` for a 24-hour (86400s) TTL.

---

### PostgreSQL (Neon) Reference Locations
Neon PostgreSQL is accessed from three locations with varying configurations:

1. **SQLAlchemy DB Connection Pool (`backend/database.py`)**:
   - Connection string is parsed via `format_neon_connection_string` to route to Neon's `-pooler` proxy (PgBouncer) and enforce transaction compatibility settings (`prepareThreshold=0` and `sslmode=require`).
   - Hardened connection settings are applied on non-SQLite configurations:
     ```python
     # backend/database.py, lines 121-127
     engine_kwargs.update({
         "pool_size":     3,     # baseline concurrent connections
         "max_overflow":  2,     # burst headroom (total max = 5, within Neon free-tier limit)
         "pool_recycle":  280,   # recycle stale connections before Neon 300s auto-suspend
         "pool_timeout":  30,    # max wait for a free slot before raising OperationalError
         "pool_pre_ping": True,  # heartbeat SELECT 1 before checkout — detects stale Neon conns
     })
     ```
   - Prepared statement caching is disabled at connection level: `prepared_statement_cache_size=0` (line 137).

2. **Synchronous Connection Shim (`core/pg_sqlite_shim.py`)**:
   - Manages a thread-safe psycopg2 connection pool:
     ```python
     # core/pg_sqlite_shim.py, lines 508-512
     min_conn = int(os.getenv("PG_POOL_MIN", "1"))
     max_conn = int(os.getenv("PG_POOL_MAX", "3"))
     min_conn = max(1, min(min_conn, 2))
     max_conn = max(min_conn, min(max_conn, 3))
     ```
   - Implements query testing (pre-ping) with `SELECT 1` on checkout.
   - Implements connection recycling at 280 seconds (under the 300s Neon idle limit).
   - Retries connection checkout 5 times with exponential backoff if `OperationalError` occurs.
   - If connecting fails after retries, fallback to local SQLite is automatically initiated:
     ```python
     # core/pg_sqlite_shim.py, lines 836-842
     try:
         return PgConnectionWrapper()
     except Exception as pg_err:
         logger.error(
             f"[DB] Failed to connect to Neon PG: {pg_err}. Falling back to SQLite."
         )
         return SqliteConnectionWrapper(target_db)
     ```

3. **Direct Asynchronous Connection Pool (`core/async_db.py`)**:
   - Uses `asyncpg` directly for managing deep-concurrency connections:
     ```python
     # core/async_db.py, lines 45-54
     connect_uri = NEON_URI.replace(
         "postgresql+asyncpg://", "postgresql://"
     )
     self.pool = await asyncpg.create_pool(
         dsn=connect_uri, min_size=1, max_size=20
     )
     ```
   - **Vulnerabilities**:
     - Does NOT rewrite the hostname to Neon's `-pooler` proxy endpoint (no pooling proxy routing).
     - Limits `max_size` to 20, exceeding the Neon free-tier maximum concurrency limit (10).
     - Does NOT disable prepared statements (`statement_cache_size` is not set to `0`), causing transaction pooling failures.
     - Does NOT implement connection recycling, pre-ping testing, or automatic fallbacks for wakeup delays.

---

### Sync Outbox & Fallback Worker Pattern
The system implements a "local-first" zero-latency write architecture:
- Outbox Table (`ps_crud_outbox`) tracked in `backend/models.py` (model `SyncOutbox`).
- When database fallback occurs, mutations are written locally to SQLite, and logged in `SyncOutbox`.
- Background Syncer (`backend/sync_worker.py`) polls `SyncOutbox` and streams changes asynchronously to the remote Neon instance using direct `asyncpg` connections with `statement_cache_size=0`.
- Connection losses during batch sync are caught and log warnings, causing the Syncer thread to poll every 30 seconds instead of 1 second until recovery.

---

## 2. Logic Chain

1. **Redis Daily Command Overhead (Rate-Limiting & Caching)**:
   - Standard routing caches routes (`FastAPICache`) and deep calculations (LLMs in `edge_cache`, ATS in `ats_matcher.py`).
   - More critically, the IP rate-limiting middleware in `web/app_v2.py` triggers an `incr` command for **every single HTTP request**. With 10,000 page views or assets fetched, the daily 10k Upstash command limit will be instantly exhausted on rate-limiting overhead alone.
   - *Therefore*, introducing a local, thread-safe, in-process rate-limiter and L1 caching layer (e.g., standard `cachetools.TTLCache` wrapped in mutual-exclusion locks) will shield Upstash Redis. Local request counting and cached results will require 0 Redis commands.

2. **ATS Matcher Blocking Hook**:
   - `core/ats_matcher.py` initializes a synchronous `redis` client. This blocks the main thread during execution and bypasses the `EdgeCache` async connection lifecycle.
   - *Therefore*, updating `full_ats_analysis` to run asynchronously and utilize the unified `edge_cache` REST interface or an async pool driver is required to eliminate sync overhead.

3. **Neon Free Tier Database Suspend**:
   - Neon serverless instances suspend after 300 seconds of inactivity. Waking up requires spin-up of the compute instance, taking 3 to 10 seconds.
   - While SQLAlchemy and the psycopg2 shim handle wakeup failures via pre-ping checking and connection retry loops, they do so synchronously inside request threads, blocking user HTTP requests and exposing them to gateway timeouts.
   - The direct `asyncpg` pool in `core/async_db.py` completely lacks statement disabling, pooler routing, pre-pings, and safe sizes, exposing it to connection exhaustions and transaction parsing crashes.
   - *Therefore*, the connection parameters in `core/async_db.py` must be hardened, and a non-blocking write-buffering strategy must be introduced. By instantly routing write mutations to a local SQLite command queue and responding with `202 Accepted`, we decouple user request latency from the Neon wakeup cold start.

---

## 3. Caveats

- **Outbox Sync Order**: When synchronizing local changes from the SQLite outbox to PostgreSQL, data collisions can occur if a tenant performs mutations concurrently across multiple application instances (split-brain state).
- **L1 In-Memory Memory footprint**: Local memory caching consumes RAM within the app server. The L1 cache must be configured with a tight max-size limit (e.g., 500 entries) and short TTL (e.g., 5 minutes) to prevent memory leakages.
- **SQLite Write Locks**: When the local SQLite database is utilized under high concurrency, WAL mode must be active to prevent table-level writing blocks.

---

## 4. Conclusion & Actionable Recommendations

### Recommendation 1: Implement Local L1 Memory Cache & Rate-Limiter Shield

Wrap `EdgeCache` in `core/edge_cache.py` with a thread-safe, in-memory cache layer. Ensure that all calls to Redis check L1 first.

*Suggested Design Sketch for `core/edge_cache.py`*:

```python
import time
import threading
from typing import Any, Dict, Optional

class L1MemoryCache:
    """Thread-safe, size-bounded in-memory L1 cache."""
    def __init__(self, maxsize: int = 500, default_ttl: int = 300):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self._cache:
                return None
            val, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl
        with self.lock:
            if len(self._cache) >= self.maxsize and key not in self._cache:
                # Evict oldest entry (FIFO)
                first_key = next(iter(self._cache))
                del self._cache[first_key]
            self._cache[key] = (value, expiry)

# Wrap EdgeCache to instantiate ShieldedCache
class ShieldedCache:
    def __init__(self, l2_redis: EdgeCache):
        self.l2 = l2_redis
        self.l1 = L1MemoryCache(maxsize=500, default_ttl=300) # 5-minute shield

    async def get(self, key: str) -> Optional[Any]:
        # 1. Query L1 (0 commands)
        val = self.l1.get(key)
        if val is not None:
            return val
        
        # 2. Query L2 (Upstash Redis)
        if self.l2.enabled:
            val = await self.l2.get(key)
            if val is not None:
                self.l1.set(key, val) # Backfill L1
                return val
        return None

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        self.l1.set(key, value, ttl=ex)
        if self.l2.enabled:
            await self.l2.set(key, value, ex=ex)
```

In addition, update the IP rate-limiting middleware in `web/app_v2.py` to use a pure local, in-memory sliding window rate limiter, entirely eliminating the per-request Upstash Redis commands:

```python
import collections

class InProcessRateLimiter:
    """Thread-safe, high-performance in-memory IP rate limiter."""
    def __init__(self, limit: int = 100, window: int = 60):
        self.limit = limit
        self.window = window
        self.requests = collections.defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        with self.lock:
            # Clean up old request timestamps
            self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]
            if len(self.requests[ip]) >= self.limit:
                return False
            self.requests[ip].append(now)
            return True
```

Update `core/ats_matcher.py` to use `ShieldedCache` asynchronously inside `full_ats_analysis`.

---

### Recommendation 2: Harden Direct asyncpg Pools (`core/async_db.py`)

Apply the same connection pooling discipline used in SQLAlchemy to the direct asyncpg pool initialization:

```python
# Proposed change to core/async_db.py, lines 40-54
if "postgres" in NEON_URI:
    try:
        import asyncpg
        from backend.database import format_neon_connection_string
        
        # Ensure pooled endpoint is used
        connect_uri = format_neon_connection_string(NEON_URI)
        connect_uri = connect_uri.replace("postgresql+asyncpg://", "postgresql://")
        
        self.pool = await asyncpg.create_pool(
            dsn=connect_uri,
            min_size=1,
            max_size=3,                      # Strictly limit to leave free-tier connection headroom
            statement_cache_size=0,          # Essential for PgBouncer transaction pooling
            max_inactive_connection_lifetime=280 # Recycle idle connections before 300s auto-suspend
        )
        self.backend = "pg"
        logger.info("APEX MATRIX: Connected to Neon Postgres via asyncpg pool.")
    except Exception as e:
        logger.error(f"Failed to connect to Neon asyncpg: {e}. Falling back to aiosqlite.")
        await self._init_sqlite()
```

---

### Recommendation 3: SQLite Failover Query Queue for Non-Blocking Write-Buffering

Implement a non-blocking queue for mutation writes when Neon is waking up or experiencing timeouts.

1. **Warmup / Non-Blocking PG Connect**:
   On startup or during failover recovery, do not block API threads connecting to PostgreSQL. Immediately route reads and writes to SQLite. Run an async background task to ping Neon; once successful, transition the connection state flag to Postgres.

2. **Pending Query Queue Schema**:
   Create a local table to store pending writes:
   ```sql
   CREATE TABLE pending_query_queue (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       query TEXT NOT NULL,
       params TEXT, -- JSON array string
       retry_count INTEGER DEFAULT 0,
       max_retries INTEGER DEFAULT 5,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       last_error TEXT
   );
   ```

3. **Background Buffer Processor**:
   A background loop inside the syncer or a dedicated worker should pull items from `pending_query_queue` and attempt execution on the PostgreSQL connection. If execution fails due to connection blocks, wait 10 seconds (giving Neon time to wake up) and retry. This guarantees that user writes are processed in sequence and eventually stored in PostgreSQL without blocking user HTTP requests.

---

## 5. Verification Method

### 1. Unit Tests Integration
Verify execution of the existing tests under different configurations:
- Check default mock fallback:
  ```bash
  pytest tests/
  ```
- Force Postgres integration test by setting env vars:
  ```bash
  $env:FORCE_PG="1"
  $env:DATABASE_URL="postgresql://user:pass@host/db"
  pytest tests/
  ```
- Force SQLite local fallback testing:
  ```bash
  $env:FORCE_SQLITE="1"
  pytest tests/
  ```

### 2. Manual Inspection Points
Verify correct configuration by inspecting database logs:
- Confirm that connection strings match the `-pooler.neon.tech` format.
- Review server startup log outputs to confirm database and cache type setups:
  - Expect: `{"msg": "Using local SQLite fallback", "url": "..."}` or `{"msg": "Connecting to remote PostgreSQL"}`
  - Expect: `{"msg": "Redis-backed API cache initialized", "max_connections": 10}`

### 3. Invalidation Conditions
- If the daily Redis command count remains high after applying L1 caching, it implies the key normalization is inconsistent (e.g. trailing whitespaces or varying casing), causing L1 misses.
- If Neon displays `OperationalError: connection limit exceeded`, it indicates that the direct connection pool in `core/async_db.py` is still configured with a high `max_size` (e.g. 20) or another server instance is exhausting pool allocations.

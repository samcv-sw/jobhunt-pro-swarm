# Handoff Report — Milestone 2: Database Pool Recycling & Connection Warmer

## 1. Observation

During read-only inspection of the active database connection pool settings across the codebase, the following files and segments were examined:

### A. `backend/database.py` (SQLAlchemy Async Engine)
* **Path**: `backend/database.py`
* **Line Range**: 60-68
* **Content**:
```python
else:
    # PostgreSQL: production-hardened pool
    engine_kwargs.update({
        "pool_size":     3,     # baseline concurrent connections
        "max_overflow":  2,     # burst headroom
        "pool_recycle":  1800,  # recycle stale connections (seconds)
        "pool_timeout":  30,    # max wait for a free slot
        "pool_pre_ping": True,  # heartbeat before checkout
    })
```
* **Status**: `pool_recycle` is set to `1800` seconds (30 minutes), which exceeds the 300-second (5-minute) Neon Serverless auto-suspend / idle timeout. `pool_pre_ping` is correctly set to `True`.

### B. `core/database.py` (SQLAlchemy Core Engine)
* **Path**: `core/database.py`
* **Line Range**: 35-44
* **Content**:
```python
from sqlalchemy.pool import NullPool

# Pool size is handled by PgBouncer; SQLAlchemy should use NullPool to prevent dual-pooling
engine = create_async_engine(
    NEON_URL,
    poolclass=NullPool,
    connect_args=connect_args,
    pool_pre_ping=True,  # Mandatory for Serverless / PgBouncer stability
    echo=False
)
```
* **Status**: Uses `NullPool`, which disables client-side connection pooling entirely. While this avoids holding dead connections, it incurs the network latency and TLS handshake cost of opening a new TCP connection on every request. No `pool_recycle` is defined.

### C. `web/shared.py` (FastAPI DB Dependency)
* **Path**: `web/shared.py`
* **Line Range**: 84-99
* **Content**:
```python
            # Configure highly-resilient Connection Pool to survive Neon Cold Starts
            if _pg_engine is None:
                from sqlalchemy import create_engine
                from sqlalchemy.pool import QueuePool
                _pg_engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=3,            # Conserve connections for free-tier concurrency limits
                    max_overflow=7,         # Allow temporary spikes during concurrent tasks
                    pool_timeout=15,        # Wait up to 15s for pool connections
                    pool_recycle=280,       # Recycle before 5min Neon auto-suspend
                    pool_pre_ping=True,     # Test connection viability before handing out
                    connect_args={
                        "connect_timeout": 10,
                        "options": "-c statement_timeout=15000"
                    }
                )
```
* **Status**: `pool_recycle` is correctly configured to `280` seconds and `pool_pre_ping` is `True`. However, this engine is **never used**. On line 102, the function directly returns `shim.connect(db_url)`, bypassing `_pg_engine` completely.

### D. `core/pg_sqlite_shim.py` (Psycopg2 Connection Shim)
* **Path**: `core/pg_sqlite_shim.py`
* **Line Range**: 461-480
* **Content**:
```python
        import time
        max_retries = 5
        for attempt in range(max_retries):
            conn = None
            try:
                conn = PG_POOL.getconn()
                conn.autocommit = True
                self.conn = conn
                BACKEND = "pg"
                break
            except psycopg2.OperationalError as e:
                if conn is not None:
                    try:
                        PG_POOL.putconn(conn, close=True)
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    raise OperationalError(e)
```
* **Status**: The psycopg2 `ThreadedConnectionPool` does not natively check connection age or execute pre-ping health checks. If Neon spins down or terminates a connection due to idle timeouts (> 300s), subsequent `getconn()` calls can return stale/closed connections, causing immediate SQL execution failures (OperationalError or InterfaceError) in the shim.

### E. `core/neon_warmer.py` & `render.yaml` (Keep-Alive Cron Job)
* **Path**: `core/neon_warmer.py`
* **Line Range**: 18-47
* **Content**: Runs as an independent script triggering `SELECT 1` on the database.
* **Path**: `render.yaml`
* **Line Range**: 52-63
* **Content**:
```yaml
  - type: cron
    name: neon-warmer
    env: python  
    plan: free
    region: oregon
    schedule: "*/5 * * * *"
    buildCommand: pip install psycopg2-binary==2.9.9
    startCommand: python core/neon_warmer.py
```
* **Status**: Running every 5 minutes (`*/5 * * * *`) via Render cron scheduler. It is **not** integrated directly with the web application or Celery workers.

---

## 2. Logic Chain

1. **Stale Connection Lifespans**:
   * Neon Serverless Postgres shuts down compute nodes after 5 minutes of idle time to conserve resources.
   * `backend/database.py` defines `pool_recycle=1800` (30 minutes). Because `1800 > 300`, connections in the pool remain active from SQLAlchemy's perspective, but are dead from Neon's perspective. When SQLAlchemy attempts to use a recycled connection after 5+ minutes of inactivity, it will fail unless `pool_pre_ping` detects it.
   * While `pool_pre_ping=True` does detect dead connections, relying on pre-ping alone causes unnecessary ping roundtrips on dead connections. Realigning `pool_recycle` to `280` ensures connections are closed cleanly on the client side before Neon terminates them.

2. **NullPool Overhead in core/database.py**:
   * `core/database.py` uses `NullPool`. This prevents stale connection errors, but forces the app to open a brand-new TCP connection on every request. This adds substantial network overhead (50-200ms latency), especially during Neon cold starts.
   * Transitioning `core/database.py` to a `QueuePool` with `pool_recycle=280` and `pool_pre_ping=True` maintains compatibility with PgBouncer transaction mode (since `statement_cache_size=0` is set), while reusing active connections to eliminate latency spikes.

3. **Shim Pool Vulnerability**:
   * The custom `PgConnectionWrapper` in `core/pg_sqlite_shim.py` uses a raw `psycopg2.pool.ThreadedConnectionPool`. This pool does not implement recycling or pre-ping.
   * When the app goes idle, the psycopg2 pool retains references to connections. When a request arrives, `getconn()` checks out a stale socket. The app immediately crashes with a `500 Internal Server Error` on the subsequent query.
   * Implementing custom recycling (closing connections older than 280 seconds) and pre-ping testing (`SELECT 1`) inside the psycopg2 checkout loop resolves this vulnerability.

4. **Warmer Sufficiency**:
   * The cron job in `render.yaml` running `core/neon_warmer.py` every 5 minutes maintains Neon compute warmth externally. There is no need to load it into FastAPI or Celery threads, keeping the core app threads clean.

---

## 3. Caveats

* **PgBouncer Transaction Mode Constraints**: In transaction mode, PgBouncer does not support prepared statements. When using a connection pool with PgBouncer, `statement_cache_size=0` must remain set in SQLAlchemy configurations (as it currently is in `core/database.py`).
* **Environment Configuration**: The `min_conn` and `max_conn` for psycopg2 are fetched via environment variables `PG_POOL_MIN` and `PG_POOL_MAX`. These should be set to conservative numbers (e.g. `min_conn=2`, `max_conn=10`) in the serverless environment to prevent exceeding Neon connection quotas.
* **SQLite Testing Isolation**: In `core/pg_sqlite_shim.py`, the function `should_use_pg` automatically bypasses PostgreSQL and uses SQLite during `unittest` or `pytest` runs to maintain test isolation. Consequently, E2E tests using `pytest` will test the SQLite path of the shim, not the PostgreSQL path, unless specifically forced with `FORCE_PG=1`.

---

## 4. Conclusion

We recommend the following exact changes to resolve Neon cold-start and idle connection spin-down errors:

### Proposal 1: `backend/database.py`
Change `pool_recycle` to `280` in the PostgreSQL connection block.
```python
<<<<
        "pool_recycle":  1800,  # recycle stale connections (seconds)
====
        "pool_recycle":  280,   # recycle stale connections (seconds)
>>>>
```

### Proposal 2: `core/database.py`
Replace `NullPool` with a resilient `QueuePool` configuration.
```python
<<<<
from sqlalchemy.pool import NullPool

# Pool size is handled by PgBouncer; SQLAlchemy should use NullPool to prevent dual-pooling
engine = create_async_engine(
    NEON_URL,
    poolclass=NullPool,
    connect_args=connect_args,
    pool_pre_ping=True,  # Mandatory for Serverless / PgBouncer stability
    echo=False
)
====
from sqlalchemy.pool import QueuePool

# Configure highly-resilient Connection Pool to survive Neon Cold Starts.
# Using QueuePool instead of NullPool to eliminate TCP handshake latency on every request.
# Conserve connections under serverless limits (pool_size=3, max_overflow=7).
engine = create_async_engine(
    NEON_URL,
    poolclass=QueuePool,
    pool_size=3,
    max_overflow=7,
    pool_timeout=15,
    pool_recycle=280,      # Recycle stale connections before 5-minute Neon suspend
    pool_pre_ping=True,    # Test connection viability before handing out
    connect_args=connect_args,
    echo=False
)
>>>>
```

### Proposal 3: `core/pg_sqlite_shim.py`
Add custom connection recycling (max age 280 seconds) and connection testing (pre-ping) inside `PgConnectionWrapper.__init__`.
```python
<<<<
        import time
        max_retries = 5
        for attempt in range(max_retries):
            conn = None
            try:
                conn = PG_POOL.getconn()
                conn.autocommit = True
                self.conn = conn
                BACKEND = "pg"
                break
            except psycopg2.OperationalError as e:
                if conn is not None:
                    try:
                        PG_POOL.putconn(conn, close=True)
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    raise OperationalError(e)
====
        import time
        max_retries = 5
        for attempt in range(max_retries):
            conn = None
            try:
                # 1. Connection Recycling: Loop to get a connection from the pool,
                # discarding any that are older than 280 seconds.
                while True:
                    conn = PG_POOL.getconn()
                    now = time.time()
                    
                    if hasattr(conn, "created_at"):
                        if now - conn.created_at > 280:
                            logger.info("[DB] Discarding expired connection in PgConnectionWrapper pool (idle > 280s).")
                            PG_POOL.putconn(conn, close=True)
                            continue  # Fetch a different connection
                    else:
                        conn.created_at = now
                    break

                # 2. Connection Testing (Pre-ping): Run a lightweight test query
                try:
                    with conn.cursor() as test_cur:
                        test_cur.execute("SELECT 1")
                except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError) as test_err:
                    logger.warning(f"[DB] Connection pre-ping failed: {test_err}. Discarding stale connection.")
                    PG_POOL.putconn(conn, close=True)
                    conn = None
                    # Raise error to trigger outer retry block with backoff
                    raise psycopg2.OperationalError("Stale connection pre-ping failed")

                conn.autocommit = True
                self.conn = conn
                BACKEND = "pg"
                break
            except psycopg2.OperationalError as e:
                if conn is not None:
                    try:
                        PG_POOL.putconn(conn, close=True)
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    raise OperationalError(e)
>>>>
```

---

## 5. Verification Method

To verify these changes independently:

1. **Verify Local Test Integrity**:
   Run the project test suite using `pytest`. The baseline test execution on the master branch was verified to complete successfully with **403 passed, 34 warnings in 65.87 seconds**:
   ```bash
   pytest
   ```
2. **Force PostgreSQL Connection Tests**:
   Run the test suite with `FORCE_PG=1` environment variable set to execute the pg_sqlite_shim's PostgreSQL paths:
   ```bash
   $env:FORCE_PG="1"
   pytest tests/test_pg_shim.py
   ```
3. **Simulate Connection Warm-Up and Recycling**:
   Review log outputs to verify that the `[DB] Discarding expired connection...` or `[DB] Connection pre-ping failed...` log messages are triggered during mock timeouts or disconnects.

# Handoff Report — Database Pooling & SQLite Fallback Audit

This report presents the findings of a comprehensive read-only audit of the database connection pooling, SQLite fallback, cold-start handling, and connection lifecycle mechanics across the backend and core services of the JobHunt Pro application.

---

## 1. Observation

Direct observations and file-level metrics gathered during the audit:

### A. Configuration & Setup
- **`.env` File**: Found `DATABASE_URL` configured to a Neon PostgreSQL instance:
  `postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require`
- **`config.py`**:
  - Line 10-11: `# Database Engine strictly enforces PostgreSQL \n # SQLite shim abolished per Enterprise Blueprint`
  - Line 169: `DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://...")`
  - Line 17: `DB_PATH = os.getenv("DB_PATH", "data/jobhunt_saas_v2.db")`
- There are **three** separate, active database managers in the codebase:
  1. `backend/database.py` (SQLAlchemy-based, yields session for web app)
  2. `core/database.py` (SQLAlchemy-based, has `Database` manager wrapper + dependency yielding)
  3. `core/async_db.py` (Custom `AsyncDatabase` using `asyncpg.create_pool` or `aiosqlite` under APEX MATRIX banner)
- Additionally, a custom compatibility driver exists at `core/pg_sqlite_shim.py` mapping DB-API requests between PG (`psycopg2`) and SQLite (`sqlite3`).

### B. Connection Pooling Settings vs. Neon Free Tier Limit (10 connections)
- **`backend/database.py`**:
  - Line 123-127:
    ```python
    "pool_size":     3,
    "max_overflow":  2,
    "pool_recycle":  280,
    "pool_timeout":  30,
    "pool_pre_ping": True,
    ```
    Total max connections per process: **5**.
- **`core/database.py`**:
  - Line 41-45:
    ```python
    pool_size=3,
    max_overflow=7,
    pool_timeout=15,
    pool_recycle=280,
    pool_pre_ping=True,
    ```
    Total max connections per process: **10**.
- **`core/async_db.py`**:
  - Line 48-50:
    ```python
    self.pool = await asyncpg.create_pool(
        dsn=connect_uri, min_size=1, max_size=20
    )
    ```
    Total max connections per process: **20** (Does not set `statement_cache_size=0`).
- **`core/pg_sqlite_shim.py`**:
  - Line 508-512:
    ```python
    min_conn = int(os.getenv("PG_POOL_MIN", "1"))
    max_conn = int(os.getenv("PG_POOL_MAX", "3"))
    ```
    Total max connections per process: **3**.

### C. Redundant Engines & Connection Pools
- **`web/shared.py`**:
  - Line 87-105:
    ```python
    if _pg_engine is None:
        from sqlalchemy import create_engine
        ...
        _pg_engine = create_engine(
            db_url,
            ...
        )
    return shim.connect(db_url)
    ```
    An engine is created and stored in the global `_pg_engine` but then ignored. The code immediately calls and returns `shim.connect(db_url)`, which creates its own `ThreadedConnectionPool` inside `core.pg_sqlite_shim`.

### D. FastAPI Generator Yield Retry Bug
- **`core/database.py`**:
  - Line 56-74:
    ```python
    async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
        retries = 5
        backoff = 1
        for attempt in range(retries):
            try:
                async with AsyncSessionLocal() as session:
                    yield session
                    break
            except OperationalError as e:
                # exponential backoff sleeps ...
    ```
    The retry loop wraps the `yield session` call. If a database query fails inside the route handler *after* the session has been successfully yielded, the generator catches the error, sleeps, and attempts to loop and `yield` a second time.

### E. Database Connection / Cursor Leaks
- **`core/pg_sqlite_shim.py`**:
  - Line 429-440:
    ```python
    def fetchone(self) -> Any | None:
        try:
            res = self.cursor.fetchone()
            if res is None:
                with contextlib.suppress(Exception):
                    self.cursor.close()
                return None
            return self._wrap_row(tuple(res))
        except Exception as e:
            with contextlib.suppress(Exception):
                self.cursor.close()
            raise e
    ```
    If `fetchone()` returns a row, the cursor is not closed, relying on garbage collection (`__del__`) to close the cursor.
  - Line 635-640:
    ```python
    def close(self) -> None:
        global PG_POOL
        if PG_POOL and self.conn:
            PG_POOL.putconn(self.conn)
            self.conn = None
    ```
    The connection is returned to the pool without verifying or closing any outstanding cursors opened during its lifecycle.
  - Cursors do not implement the `__enter__` and `__exit__` context manager protocol, preventing the use of `with conn.cursor() as cur:` syntax on PG wrappers.

### F. Sync Worker Timeouts & Cold-Starts
- **`backend/sync_worker.py`**:
  - Line 237-241:
    ```python
    cloud_conn = await _connect_with_retry(
        pgbouncer_url,
        ssl="require",
        statement_cache_size=0,
    )
    ```
    No `server_settings={"statement_timeout": "..."}` or client-side `timeout` is passed to the connection constructor.
  - Line 102-111:
    ```python
    except Exception as exc:
        last_exc = exc
        if _TOO_MANY_CONNS and isinstance(exc, _TOO_MANY_CONNS):
            continue
        raise
    ```
    The worker only retries on `TooManyConnectionsError`. Other connection exceptions (e.g. `PostgresConnectionError` or `TimeoutError` caused by a Neon cold start) fail immediately, causing the outer worker loop to catch the exception and sleep for **30 seconds** (Line 292) before attempting to reconnect.

### G. Import Crash vulnerability in `core/database.py`
- **`core/database.py`**:
  - Line 38: Runs `create_async_engine(NEON_URL, ...)` at import time.
  - If `DATABASE_URL` is not set or empty, this call raises `sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from string ''` immediately during Python import.
  - While relative imports via the package `core` transitively load `.env` (due to `core/__init__.py` -> `ats_matcher.py` -> `config.py` -> `load_dotenv`), direct imports (e.g., from unit tests or standalone scripts) will crash at import time if `DATABASE_URL` is absent.

---

## 2. Logic Chain

1. **Neon Limit Exhaustion**: Neon's free tier imposes a strict 10-connection limit. Combining `backend/database.py` (max 5), `core/database.py` (max 10), and `core/async_db.py` (max 20) in a multi-process environment (or even in a single process executing concurrent tasks) will exceed 10 connections. This triggers `TooManyConnectionsError` on subsequent requests.
2. **PgBouncer Failures**: PgBouncer transaction-mode pools reject named prepared statements. Because `core/async_db.py` creates its pool without `statement_cache_size=0`, executing queries via `async_db` will crash on PgBouncer with `FeatureNotSupported` errors under concurrent request patterns.
3. **Redundant Resource Usage**: `web/shared.py` initializes a SQLAlchemy connection pool (`_pg_engine`) but immediately bypasses it to use `pg_sqlite_shim`'s independent pool. This wastes connection slots on the Neon server.
4. **FastAPI Generator Lifecycle Crash**: In `get_db_session()`, the generator yields control to FastAPI's route. If a query inside the route fails with `OperationalError`, control flows back into the generator's `except` block. Since the loop iterator is active, it runs again, creates a new session, and yields it. This triggers a `RuntimeError` (generator raised StopIteration / unexpected yield) inside FastAPI, masking the original error and leaking the old session.
5. **Cold-Start Latency Amplification**: If Neon goes to sleep, the first request wakes it up. `sync_worker.py` attempts a connection, experiences a cold-start timeout/error, and aborts immediately (since it only retries on `TooManyConnectionsError`). It then sleeps for 30 seconds. A 3-second cold start is thus amplified into a 30-second synchronization delay.
6. **Leak Accumulation**: Because `PgCursorWrapper.fetchone()` does not close the cursor on row retrieval and `PgConnectionWrapper.close()` does not close open cursors, applications executing raw SQL queries (like `core/job_queue.py`'s `dequeue_task` or `fail_task`) leak open cursors on the Postgres server, accumulating resources until garbage collection fires.

---

## 3. Caveats

- **Network Constraints**: The audit was performed in CODE_ONLY network mode. External database latency, firewall behaviors, or actual Neon cluster response times could not be dynamically monitored.
- **Supabase Mode**: `web/app_v2.py` references a `SUPABASE_MODE` switch that swaps the pg-sqlite shim for `core.supabase_rest_shim`. This shim was not fully analyzed as it was out of scope for Neon connection pooling and SQLite fallbacks.
- **Other Clients**: Third-party packages or system-level scripts might open connections to Neon independently, reducing the available connection slots below the expected 10.

---

## 4. Conclusion

The Neon DB connection pooling and SQLite fallback logic are partially configured correctly but suffer from critical vulnerabilities under production load:
1. **High Risk of Connection Exhaustion**: Connection pool configurations in `core/database.py` and `core/async_db.py` are set too high (10 and 20 respectively), easily exceeding Neon's 10-connection limit.
2. **PgBouncer Incompatibility**: `core/async_db.py` lacks statement caching disabling, causing query failures under PgBouncer transaction pooling.
3. **FastAPI Route Crashes**: The generator retry loop in `core/database.py` is structurally bugged and will cause FastAPI crashes on query operational errors.
4. **Resource Leaks**: The pg-sqlite shim leaks database cursors when queries successfully retrieve rows.
5. **Slow Recovery on Cold Starts**: The background sync worker introduces artificial 30-second delays upon encountering Neon cold starts.

A patch containing proposed fixes for these issues is available at:
`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_2\proposed_fixes.patch`

---

## 5. Verification Method

To verify these findings and the proposed fixes:
1. Run the existing test suites to confirm basic functionality is not broken:
   - `pytest tests/e2e/test_database.py` (verified: 6 passed)
   - `pytest tests/test_pg_shim.py` (verified: 9 passed)
2. Verify the import crash by running python import in an isolated environment without environment variables:
   - `python -c "import os; os.environ.clear(); import core.database"` (will crash under original code due to `create_async_engine('')`).
3. Inspect `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_2\proposed_fixes.patch` to verify alignment with findings and structural validity.

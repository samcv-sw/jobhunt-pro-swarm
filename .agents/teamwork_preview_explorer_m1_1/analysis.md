# Comprehensive Analysis of Database Auto-Detection, Fallback, Pooling, and Query Translation

## Executive Summary
This report presents a forensic investigation of the database architecture across `core/database.py`, `core/pg_sqlite_shim.py`, `backend/database.py`, `config.py`, and `core/async_db.py` within **JobHunt Pro SaaS**.

The system is designed to support 24/7 continuous operation on $0 free-tier cloud infrastructure (Neon PostgreSQL, Supabase, Turso) with seamless local SQLite fallback. While the existing connection pooling and query translation mechanisms (`convert_sql`) demonstrate high sophistication (handling `?` to `%s`, `INSERT OR REPLACE` to `ON CONFLICT`, `datetime` functions, and connection recycling at 280s), critical gaps exist that prevent 100% seamless zero-crash auto-detection and fallback.

---

## 1. Environment Variable Ingestion Matrix

`PROJECT.md` specifies the interface contract:
> "Detects `DATABASE_URL` / `POSTGRES_URL` in environment. If present, connects to PostgreSQL; otherwise falls back to SQLite."

The investigation revealed significant fragmentation and inconsistencies across files in how environment variables are read:

| Environment Variable | `config.py` | `core/database.py` | `core/pg_sqlite_shim.py` | `backend/database.py` | `core/async_db.py` | Status / Gap |
|---|---|---|---|---|---|---|
| `DATABASE_URL` | Read (Default: local PG string) | Read | Read | Read | Read | Config default breaks SQLite fallback |
| `POSTGRES_URL` | ❌ Not read | ❌ Not read | ❌ Not read | ❌ Not read | ❌ Not read | **CRITICAL GAP**: Violates `PROJECT.md` contract |
| `NEON_URL` | Read (Defaults to `DATABASE_URL`) | ❌ Not read | Read | ❌ Not read | Read | Inconsistent reading |
| `DATABASE_URL_SYNC` | ❌ Not read | ❌ Not read | Read | ❌ Not read | Read | Inconsistent reading |
| `LOCAL_DATABASE_URL` | ❌ Not read | Read | ❌ Not read | Read | ❌ Not read | Inconsistent reading |
| `TURSO_DATABASE_URL` | Read | ❌ Not read | ❌ Not read | Read | ❌ Not read | Used only in `backend/database.py` & `web/app_v2.py` |
| `FORCE_PG` | ❌ Not read | ❌ Not read | Read (`FORCE_PG=1`) | ❌ Not read | ❌ Not read | Shim-only flag |
| `FORCE_SQLITE` | ❌ Not read | ❌ Not read | Read (`FORCE_SQLITE=1`) | ❌ Not read | Read (`FORCE_SQLITE=1`) | Inconsistent reading |
| `DB_PATH` / `SQLITE_PATH` | Read (`DB_PATH`) | ❌ Not read | ❌ Not read | ❌ Not read | Read (`SQLITE_PATH`) | Variable name mismatch |

### Critical Finding: `config.py` False-Positive Default
In `config.py` (line 169):
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://jobhunt:jobhunt_password@localhost:5432/jobhunt_db")
NEON_URL = os.getenv("NEON_URL", DATABASE_URL)
```
When `DATABASE_URL` is **not set** in the environment (e.g., in a clean local environment or simple deployment), `config.DATABASE_URL` evaluates to `postgresql+asyncpg://jobhunt:jobhunt_password@localhost:5432/jobhunt_db`. Any module importing `config.DATABASE_URL` or `config.NEON_URL` treats PostgreSQL as configured and attempts to connect to `localhost:5432`, crashing instead of defaulting to SQLite.

---

## 2. Database Backend Auto-Detection & Fallback Flow

### A. `core/pg_sqlite_shim.py` (Synchronous DB-API Layer)
- **Detection Routine**: `_raw_uri` resolves `NEON_URL` || `DATABASE_URL` || `DATABASE_URL_SYNC`.
- **URI Formatting**: `format_neon_connection_string()` checks for `neon.tech` hostnames, appends `-pooler` if absent, sets `sslmode=require` and `prepareThreshold=0`. `clean_psycopg2_uri()` strips `prepareThreshold` for `psycopg2` compatibility.
- **Routing Decision (`should_use_pg`)**:
  1. If running under `pytest` or `unittest`, returns `False` (forces SQLite for test isolation).
  2. If `FORCE_PG=1`, returns `True`.
  3. If `db_path` starts with `postgresql://`, `postgres://`, or `postgresql+asyncpg://`, returns `True`.
  4. If `db_path` contains `:memory:`, `backup`, or `temp`, returns `False`.
  5. If `NEON_URI` is set AND `db_path` matches main DB patterns (`jobhunt`, `saas`, `database`), returns `True`.
- **Runtime Fallback**: In `connect()`, `PgConnectionWrapper()` is instantiated. If `psycopg2.OperationalError` or any Exception occurs during pool creation or checkout, it catches the exception, logs a warning, and returns `SqliteConnectionWrapper(sqlite_db)`. **This is the gold standard runtime fallback pattern in the codebase.**

### B. `core/database.py` (SQLAlchemy Async Engine Layer)
- **Detection Routine**: `NEON_URL = os.getenv("DATABASE_URL", "")`. Replaces `postgresql://` or `postgres://` with `postgresql+asyncpg://`.
- **Routing Decision**: `IS_SQLITE = not NEON_URL or "sqlite" in NEON_URL`. Fallback path: `sqlite+aiosqlite:///./data/jobhunt_saas_v2.db`.
- **Resilience**: `get_db_session()` uses exponential backoff (5 retries: 1s, 2s, 4s, 8s, 16s with jitter) to retry `AsyncSessionLocal()` creation when `sqlalchemy.exc.OperationalError` occurs during Neon cold starts.
- **Gaps**: Does NOT call `format_neon_connection_string()` (misses pooler hostname formatting). Does NOT check `POSTGRES_URL` or `NEON_URL` env vars directly.

### C. `backend/database.py` (SQLAlchemy Async Engine for REST API)
- **Detection Priority**:
  1. `TURSO_DATABASE_URL` (libsql edge DB)
  2. `REMOTE_PG_URL` (`format_neon_connection_string(os.getenv("DATABASE_URL"))`)
  3. `LOCAL_DB_URL` (`sqlite+aiosqlite:///./data/jobhunt_saas_v2.db`)
- **Resilience**: Features `warmup_db()` which executes async `SELECT 1` across `pool_size` connections during application startup to wake up Neon from 300s serverless sleep.
- **Gaps**: Missing dynamic runtime fallback! If `DATABASE_URL` is set but PostgreSQL is unreachable at runtime, `create_async_engine` fails or requests throw `OperationalError` on every session yield without reverting to `LOCAL_DB_URL`.

---

## 3. Connection Pooling Architecture & Lifecycles

### A. PostgreSQL Pool Hardening (Neon 300s Serverless Suspend Protection)
Neon free-tier databases suspend after 300 seconds (5 minutes) of inactivity. Both `core/pg_sqlite_shim.py`, `core/database.py`, and `backend/database.py` implement specific pooling strategies to prevent stale connection crashes:

1. **`core/pg_sqlite_shim.py` (`PgConnectionWrapper`)**:
   - Pool: `psycopg2.pool.ThreadedConnectionPool(min_conn=1, max_conn=3)`
   - PID Fork Safety: Tracks `POOL_PID = os.getpid()`. If `os.getpid() != POOL_PID` (e.g. process fork under Gunicorn/Uvicorn multi-worker), closes inherited pool and re-creates a process-local pool.
   - 280s Connection Recycling: Checks `now - connection._created_at > 280`. Discards idle connection before Neon's 300s suspend window.
   - Pre-Ping Heartbeat: Runs `cursor.execute("SELECT 1")` before returning connection to caller.
2. **`core/database.py` & `backend/database.py` (SQLAlchemy QueuePool)**:
   - `pool_size = 2` (or 3), `max_overflow = 1` (respects Neon 10-connection limit).
   - `pool_recycle = 280` (recycles connections at 280s).
   - `pool_pre_ping = True` (executes `SELECT 1` on checkout).
   - `statement_cache_size = 0` / `prepared_statement_cache_size = 0` (prevents PgBouncer transaction mode errors).

### B. SQLite Pragmas & High-Performance Storage Settings
When operating on SQLite fallback:
- **`core/pg_sqlite_shim.py`**:
  - Detects PythonAnywhere NFS (`PYTHONANYWHERE_SITE` or `PYTHONANYWHERE_DOMAIN`). On PythonAnywhere, forces `PRAGMA journal_mode=DELETE` and `PRAGMA synchronous=FULL` (prevents WAL lock issues on network storage). On local/cloud disks, uses `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL`.
  - Sets `cache_size=-64000` (64MB RAM cache), `temp_store=MEMORY`, `mmap_size=268435456` (256MB memory mapped I/O), `busy_timeout=30000` (30s wait on locks).
- **`core/database.py` & `backend/database.py`**:
  - Listens to engine `connect` event and sets `journal_mode=WAL`, `synchronous=NORMAL`, `cache_size=-2000`, `temp_store=MEMORY`.
  - **Gap**: Missing PythonAnywhere check! Unconditionally forces WAL mode on `core/database.py` and `backend/database.py`, which causes file locking errors on PythonAnywhere NFS.

---

## 4. Query Translation Engine Analysis

### A. SQLite → PostgreSQL Translation (`convert_sql` in `core/pg_sqlite_shim.py`)
`convert_sql()` translates SQLite dialect queries into PostgreSQL-compatible SQL:

1. **Positional Placeholders**: Converts unquoted `?` to `%s` for `psycopg2`.
2. **Auto-Increment Primary Keys**: Converts `INTEGER PRIMARY KEY AUTOINCREMENT` to `SERIAL PRIMARY KEY`.
3. **Insert Conflict Handling**:
   - `INSERT OR REPLACE INTO tbl (col1, col2) VALUES (...)` → `INSERT INTO tbl (col1, col2) VALUES (...) ON CONFLICT (col1) DO UPDATE SET col2 = EXCLUDED.col2`
   - `INSERT OR IGNORE INTO ...` → `INSERT INTO ... ON CONFLICT DO NOTHING`
4. **Sequence & Identity Functions**:
   - `last_insert_rowid()` → `lastval()`
   - Appends `RETURNING id` to `INSERT` statements for primary tables (`users`, `leads`, `job_applications`, `sent_emails`, etc.) and sets `cursor.lastrowid` from the returned tuple.
5. **Datetime & Timestamp Functions**:
   - `datetime('now', '+7 days')` → `NOW() + INTERVAL '7 days'`
   - Supports dynamic interval strings e.g. `datetime('now', '+' || ? || ' minutes')` → `NOW() + (?)::INTERVAL`
   - `strftime('%s', 'now')` → `EXTRACT(EPOCH FROM NOW())`
   - `strftime('%Y-%m-%d', col)` → `TO_CHAR(col, '%Y-%m-%d')`
   - `DATETIME` data type → `TIMESTAMP`
   - `CURRENT_TIMESTAMP` → `NOW()`
6. **PRAGMA & Metadata Queries**:
   - `PRAGMA table_info('tbl')` → `SELECT ordinal_position, column_name, data_type... FROM information_schema.columns WHERE table_name = 'tbl'`
   - General `PRAGMA ...` → empty string `""` (bypassed)
   - `sqlite_master` → `information_schema.tables`
7. **Case-Insensitive Pattern Matching**:
   - `LIKE` → `ILIKE`

### B. PostgreSQL → SQLite Translation (`_translate_for_sqlite` in `core/pg_sqlite_shim.py`)
When PostgreSQL queries are passed to SQLite fallback:
1. `ILIKE` → `LIKE`
2. Strips PostgreSQL `::type` casts (e.g. `col::integer` → `col`)
3. Strips `RETURNING` clause (e.g. `RETURNING id` → `""`)

### C. **CRITICAL GAP**: Missing `$1/$2` to `?` Parameter Conversion in `SqliteConnectionWrapper`
`PROJECT.md` contract states:
> "Auto-translates SQL placeholders $1, $2 to ? for SQLite compatibility."

While `core/async_db.py` converts `?` to `$1, $2` via `_convert_query_to_pg()`, `core/pg_sqlite_shim.py`'s `_translate_for_sqlite()` **lacks code to convert `$1, $2, $3` back to `?`**.
If any component passes PostgreSQL positional parameters (`$1, $2`) to `SqliteConnectionWrapper.execute()`, SQLite fails with:
`sqlite3.OperationalError: near "$1": syntax error`

---

## 5. Summary of Identified Gaps for 100% Zero-Crash Auto-Detection

### Gap 1: `POSTGRES_URL` Environment Variable Unhandled
- **Location**: `config.py`, `core/database.py`, `backend/database.py`, `core/pg_sqlite_shim.py`, `core/async_db.py`.
- **Root Cause**: `POSTGRES_URL` (exported by platforms like Supabase, Vercel Postgres, Railway) is omitted from environment resolution lists.
- **Impact**: Automatic detection fails on platforms providing `POSTGRES_URL` instead of `DATABASE_URL`.

### Gap 2: `config.py` Hardcoded PostgreSQL Fallback String
- **Location**: `config.py:169`.
- **Root Cause**: `DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://jobhunt:jobhunt_password@localhost:5432/jobhunt_db")`.
- **Impact**: In environments without `DATABASE_URL`, `config.DATABASE_URL` is truthy and points to local PostgreSQL, blocking auto-detection fallback to SQLite.

### Gap 3: Missing `$1/$2` to `?` Parameter Translation in `_translate_for_sqlite()`
- **Location**: `core/pg_sqlite_shim.py:755`.
- **Root Cause**: `_translate_for_sqlite()` translates `ILIKE`, `::type`, and `RETURNING`, but does not convert numeric parameters `$1, $2, ...` to `?`.
- **Impact**: Queries formatted with `$1, $2` fail under SQLite fallback.

### Gap 4: `backend/database.py` Lacks Dynamic Runtime SQLite Fallback
- **Location**: `backend/database.py:80-100`.
- **Root Cause**: `ACTIVE_DB_URL` is resolved once at module load. If PostgreSQL is unreachable at runtime, `get_db()` raises `OperationalError` without falling back to `LOCAL_DB_URL`.
- **Impact**: Outages or network flickers cause total backend crash instead of seamless SQLite fallback.

### Gap 5: Inconsistent Neon URI Formatting in `core/database.py`
- **Location**: `core/database.py:14-18`.
- **Root Cause**: `core/database.py` does not call `format_neon_connection_string()`, whereas `core/pg_sqlite_shim.py` and `backend/database.py` do.
- **Impact**: Direct Neon connections in `core/database.py` miss automatic `-pooler` domain suffix insertion and parameter cleaning.

### Gap 6: `format_neon_connection_string` Host Subdomain & Fixed Port Edge Cases
- **Location**: `core/pg_sqlite_shim.py:49-60` & `backend/database.py:45-60`.
- **Root Cause**: Splicing `-pooler` onto `hostname.split('.', 1)` can corrupt custom Neon CNAME domains or non-standard subdomains, and hardcoding `:5432` overwrites custom database ports.
- **Impact**: Connection failure on non-standard PostgreSQL ports or custom CNAME proxy URLs.

### Gap 7: Unconditional WAL Mode on Network Storage (PythonAnywhere)
- **Location**: `core/database.py:70` & `backend/database.py:163`.
- **Root Cause**: `core/database.py` and `backend/database.py` set `PRAGMA journal_mode=WAL` without checking if running on PythonAnywhere NFS storage.
- **Impact**: `database is locked` operational errors on PythonAnywhere.

---

## 6. Verification & Test Strategy
To verify zero-crash auto-detection and query translation integrity:

1. **Unit & Integration Test Suite**:
   Run existing pytest suite with:
   `pytest`
2. **Environment Variable Permutations**:
   - `DATABASE_URL` unset, `POSTGRES_URL` unset → Expect SQLite fallback (`data/jobhunt_saas_v2.db`).
   - `POSTGRES_URL=postgresql://...` set → Expect PostgreSQL auto-detection.
   - Invalid `DATABASE_URL` set (unreachable host) → Expect fallback to SQLite without uncaught exception.
3. **Query Parameter Translation Tests**:
   - Pass queries with `$1, $2` to `SqliteConnectionWrapper` → Verify successful execution without syntax error.
   - Pass queries with `?` to `PgConnectionWrapper` → Verify conversion to `%s` and execution.

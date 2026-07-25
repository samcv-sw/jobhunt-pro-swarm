# Handoff Report — Database Auto-Detection & Fallback Analysis

## 1. Observation
Direct inspection of `config.py`, `core/database.py`, `core/pg_sqlite_shim.py`, `backend/database.py`, and `core/async_db.py` yielded the following facts:

1. **`config.py` (Line 169-170)**:
   ```python
   DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://jobhunt:jobhunt_password@localhost:5432/jobhunt_db")
   NEON_URL = os.getenv("NEON_URL", DATABASE_URL)
   ```
   `config.DATABASE_URL` provides a default PostgreSQL URL when `DATABASE_URL` is omitted from environment variables. `POSTGRES_URL` is not checked.

2. **`core/database.py` (Lines 14-23)**:
   ```python
   NEON_URL = os.getenv("DATABASE_URL", "")
   if NEON_URL.startswith("postgresql://"):
       NEON_URL = NEON_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
   elif NEON_URL.startswith("postgres://"):
       NEON_URL = NEON_URL.replace("postgres://", "postgresql+asyncpg://", 1)
   IS_SQLITE = not NEON_URL or "sqlite" in NEON_URL
   ```
   Reads only `DATABASE_URL`. Does not read `POSTGRES_URL` or `NEON_URL` env vars. Does not format host with `format_neon_connection_string`. Unconditionally applies WAL mode on SQLite connect (Line 70).

3. **`core/pg_sqlite_shim.py` (Lines 107-116, 755-770, 880-915)**:
   ```python
   _raw_uri = (
       os.getenv("NEON_URL")
       or os.getenv("DATABASE_URL")
       or os.getenv("DATABASE_URL_SYNC")
       or ""
   )
   ```
   - Missing `POSTGRES_URL` in `_raw_uri` list.
   - `_translate_for_sqlite(query)` replaces `ILIKE` → `LIKE`, strips `::type` casts and `RETURNING` clauses, but does **not** translate `$1, $2, ...` positional parameters to `?`.
   - `connect()` catches `Exception` during `PgConnectionWrapper()` creation and successfully falls back to `SqliteConnectionWrapper(sqlite_db)` (Lines 908-914).

4. **`backend/database.py` (Lines 72-97)**:
   ```python
   TURSO_URL = os.getenv("TURSO_DATABASE_URL")
   LOCAL_DB_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./data/jobhunt_saas_v2.db")
   REMOTE_PG_URL = (
       format_neon_connection_string(os.getenv("DATABASE_URL")) if os.getenv("DATABASE_URL") else None
   )
   ```
   Reads `TURSO_DATABASE_URL`, `DATABASE_URL`, and `LOCAL_DATABASE_URL`. Ignores `POSTGRES_URL`, `NEON_URL`, `DATABASE_URL_SYNC`. Resolves `ACTIVE_DB_URL` once at module load time; if PostgreSQL connection fails at runtime, `get_db()` raises `OperationalError` without falling back to `LOCAL_DB_URL`.

5. **`core/async_db.py` (Lines 9-14)**:
   ```python
   NEON_URI = (
       os.getenv("NEON_URL")
       or os.getenv("DATABASE_URL")
       or os.getenv("DATABASE_URL_SYNC")
       or ""
   )
   ```
   Ignores `POSTGRES_URL`. Translates `?` → `$1, $2` for `asyncpg`.

---

## 2. Logic Chain

1. **`POSTGRES_URL` Unhandled**:
   - *Observation*: `PROJECT.md` specifies `DATABASE_URL` / `POSTGRES_URL` detection contract, but no file in the codebase reads `os.getenv("POSTGRES_URL")`.
   - *Deduction*: When deployed on hosting platforms that provide `POSTGRES_URL` (e.g. Supabase, Vercel, Railway), the system fails to detect the remote PostgreSQL database and defaults to local SQLite.

2. **`config.py` Default Collision**:
   - *Observation*: `config.py` sets a default PostgreSQL connection string when `DATABASE_URL` is empty.
   - *Deduction*: Modules reading `config.DATABASE_URL` assume PostgreSQL is available even when no database environment variable is provided, attempting to connect to `localhost:5432` and failing instead of using SQLite.

3. **`$1/$2` Parameter Breakdown on SQLite Fallback**:
   - *Observation*: `convert_sql` translates `?` → `%s` for PostgreSQL in `PgCursorWrapper`, but `_translate_for_sqlite` in `SqliteConnectionWrapper` does not translate `$1, $2` → `?`.
   - *Deduction*: If code structured with PostgreSQL `$1, $2` parameters runs under SQLite fallback, SQLite execution throws `sqlite3.OperationalError: near "$1": syntax error`.

4. **Lack of Dynamic Fallback in `backend/database.py`**:
   - *Observation*: `backend/database.py` fixes `ACTIVE_DB_URL` at import time.
   - *Deduction*: If `DATABASE_URL` is present but the database server is temporarily down or unreachable, `backend/database.py` sessions will fail on every request without attempting `LOCAL_DB_URL`.

5. **SQLite Journal Mode Locking on NFS**:
   - *Observation*: `core/database.py` and `backend/database.py` force `PRAGMA journal_mode=WAL` without checking for PythonAnywhere environment variables, whereas `core/pg_sqlite_shim.py` checks `PYTHONANYWHERE_SITE`.
   - *Deduction*: Running `core/database.py` or `backend/database.py` on PythonAnywhere leads to `database is locked` errors due to NFS filesystem limitations with WAL mode.

---

## 3. Caveats

- **Uninvestigated Areas**: Specific cloud deployment logs (Vercel/Render live environment runtime outputs) were not inspected directly as this is a local static codebase analysis.
- **Assumptions**: Assumed standard behaviour of `psycopg2`, `asyncpg`, `aiosqlite`, and `libsql_experimental` based on Python type signatures and imports.
- **Alternative Interpretations Considered**: `config.py`'s default PostgreSQL URL may have been intended for local docker-compose setups, but it conflicts with the auto-detection fallback contract.

---

## 4. Conclusion

The database layer exhibits strong connection pooling resilience (PID fork resetting, 280s connection recycling before Neon's 300s suspend, pre-ping heartbeats) and comprehensive query translation (`convert_sql`). However, 7 distinct gaps must be addressed to achieve 100% zero-crash auto-detection and seamless fallback:

1. Add `POSTGRES_URL` to environment resolution chains across all 5 files.
2. Remove hardcoded PostgreSQL default in `config.py` (default to `""` or `LOCAL_DATABASE_URL`).
3. Implement `$1, $2, ...` → `?` translation in `_translate_for_sqlite()` within `core/pg_sqlite_shim.py`.
4. Implement dynamic runtime fallback in `backend/database.py` when PostgreSQL initialization/execution fails.
5. Standardize Neon URI host pooler formatting by calling `format_neon_connection_string` in `core/database.py`.
6. Preserving custom database ports in `format_neon_connection_string`.
7. Add PythonAnywhere NFS detection (`journal_mode=DELETE`) to `core/database.py` and `backend/database.py`.

---

## 5. Verification Method

1. **Inspect Analysis Report**:
   Read `analysis.md` in `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1\analysis.md`.

2. **Run Pytest Verification**:
   Execute pytest to ensure existing tests remain green:
   `pytest`

3. **Check Code Locations**:
   - `config.py` line 169
   - `core/database.py` lines 14-23, 70
   - `core/pg_sqlite_shim.py` lines 107-116, 755-770
   - `backend/database.py` lines 72-97

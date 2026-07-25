# Handoff Report — Milestone 1 Code Review & Stress Test

## 1. Observation

A detailed line-by-line review and empirical stress testing were conducted on the five Milestone 1 files:
- `config.py`
- `core/database.py`
- `core/pg_sqlite_shim.py`
- `backend/database.py`
- `core/async_db.py`

### Key Code & Diagnostic Findings:

1. **Inconsistent `POSTGRES_URL` Priority in `config.py`** (`config.py:169` vs Database Engines):
   - In `config.py:169`:
     ```python
     DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("NEON_URL") or "sqlite:///./data/jobhunt_saas_v2.db"
     ```
   - In `core/database.py:66`, `core/pg_sqlite_shim.py:107`, `backend/database.py:75`, and `core/async_db.py:9`:
     `POSTGRES_URL` is prioritized *before* `DATABASE_URL`:
     ```python
     os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or os.getenv("NEON_URL")
     ```
   - **Observation**: When `.env` contains `DATABASE_URL=sqlite:///...` and `POSTGRES_URL=postgres://...` is exported in the environment, `config.DATABASE_URL` remains set to SQLite, while all 4 database engines connect to PostgreSQL, causing a configuration mismatch.

2. **Runtime Generator Failure on Fallback in `backend/database.py`** (`backend/database.py:208-237`):
   - `get_db()` is implemented as a FastAPI generator dependency:
     ```python
     async def get_db():
         ...
         try:
             session = async_session()
             yield session
         except Exception as exc:
             ...
             if "sqlite" not in ACTIVE_DB_URL and ...:
                 _switch_to_sqlite_fallback()
                 async with async_session() as fallback_session:
                     yield fallback_session
     ```
   - **Observation**: Yielding a second time (`yield fallback_session`) from a single generator dependency after catching an exception raises `RuntimeError: generator didn't stop` in Starlette/FastAPI, causing request failure instead of transparent fallback execution.

3. **Naive String-Split Parameter Conversion in `core/async_db.py`** (`core/async_db.py:121-129`):
   - In `AsyncDatabase._convert_query_to_pg`:
     ```python
     parts = query.split("?")
     if len(parts) == 1: return query
     result = parts[0]
     for i, part in enumerate(parts[1:], 1):
         result += f"${i}" + part
     ```
   - **Observation**: Executing `_convert_query_to_pg("SELECT * FROM jobs WHERE title = 'What?' AND id = ?")` outputs `"SELECT * FROM jobs WHERE title = 'What$1' AND id = $2"`. Naive splitting converts question marks inside string literals into `$1` and shifts parameter position indices.

4. **Unquoted Parameter Regex Sub in `core/pg_sqlite_shim.py`** (`core/pg_sqlite_shim.py:761`):
   - In `SqliteConnectionWrapper._translate_for_sqlite`:
     ```python
     query = re.sub(r"\$\d+", "?", query)
     ```
   - **Observation**: Executing `_translate_for_sqlite("SELECT * FROM jobs WHERE price = '$100' AND id = $1")` replaces `$100` inside string literal `'$100'` with `'?'`, resulting in `"SELECT * FROM jobs WHERE price = '?' AND id = ?"`.

5. **NFS & PythonAnywhere WAL Mode Guard (PASSED)**:
   - Verified across `core/database.py`, `core/pg_sqlite_shim.py`, `backend/database.py`, and `core/async_db.py`. All modules check `PYTHONANYWHERE_SITE`, `PYTHONANYWHERE_DOMAIN`, `NFS_MODE`, and `DISABLE_WAL`, correctly switching SQLite to `PRAGMA journal_mode=DELETE` and `PRAGMA synchronous=FULL` when on NFS.

6. **Integrity Violations Check (PASSED)**:
   - No hardcoded test results, facade implementations, or fake mocks were found in the core database source files.

---

## 2. Logic Chain

1. **Step 1 (Environment Priority)**: `config.py` serves as the central configuration module for the application. Because line 169 checks `os.getenv("DATABASE_URL")` before `os.getenv("POSTGRES_URL")`, any default `.env` setting `DATABASE_URL` locks `config.DATABASE_URL` to SQLite even when `POSTGRES_URL` is configured for production. Mismatched database targets lead to subtle routing bugs across services.
2. **Step 2 (FastAPI Dependency Lifecycles)**: FastAPI generator dependencies expect a single `yield` statement corresponding to the lifecycle of an HTTP request. Yielding a fallback session inside the exception handler breaks Starlette's generator protocol.
3. **Step 3 (SQL Translation Correctness)**: SQL parameter translation must be quote-aware. Performing raw regex replacements or unquoted string splits on `?` or `$N` mutates valid string literals containing `?` or `$` characters, triggering SQL syntax or bind error exceptions at runtime.

---

## 3. Caveats

- **Pytest Isolation**: `core/pg_sqlite_shim.py` includes a `should_use_pg` check that explicitly disables PostgreSQL during test runs (`"pytest" in sys.modules`). This is a deliberate protection mechanism for local testing, though `FORCE_PG=1` can override it.
- **PgBouncer Constraints**: `statement_cache_size=0` / `prepared_statement_cache_size=0` are correctly applied in `core/database.py`, `core/pg_sqlite_shim.py`, and `core/async_db.py` to prevent transaction-pooled connection errors on Neon/PgBouncer.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

While the core architectural foundation (Neon pool recycling, statement cache tuning, cold-start backoff, and NFS safety guards) is sound, four specific defects must be addressed prior to approval:

1. **Fix `config.py:169`**: Align environment variable priority order with database modules: `os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or os.getenv("NEON_URL")`.
2. **Refactor `backend/database.py:get_db()`**: Remove the inner `yield fallback_session` from inside the exception block of the generator dependency to prevent ASGI generator runtime errors.
3. **Quote-Aware Parameter Parsing in `core/async_db.py`**: Update `_convert_query_to_pg` to ignore `?` characters inside single/double quotes (matching `convert_sql` in `pg_sqlite_shim.py`).
4. **Quote-Aware Parameter Parsing in `core/pg_sqlite_shim.py`**: Update `_translate_for_sqlite` to avoid replacing `$N` parameters that appear inside string literals.

---

## 5. Verification Method

To verify the findings independently:

1. **Test `config.py` Priority Mismatch**:
   ```bash
   python -c "import os; os.environ['DATABASE_URL']='sqlite:///test.db'; os.environ['POSTGRES_URL']='postgres://user:pass@host/db'; import config; print('config:', config.DATABASE_URL)"
   ```
   *Expected result currently*: Prints `sqlite:///test.db` instead of `postgres://...`.

2. **Test Parameter Translation with Quoted Literals**:
   ```bash
   python -c "from core.async_db import async_db; print(async_db._convert_query_to_pg(\"SELECT * FROM t WHERE name = 'What?' AND id = ?\"))"
   ```
   *Expected result currently*: Outputs `SELECT * FROM t WHERE name = 'What$1' AND id = $2` (corrupted literal).

3. **Run Unit & E2E Test Suite**:
   ```bash
   pytest tests/e2e/test_database.py
   ```

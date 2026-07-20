import logging
import os
import re
import sqlite3 as real_sqlite3
import weakref
from collections.abc import Iterable, Iterator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)


def _safe_str(val: Any) -> str:
    """Sanitize string for safe logging in windows environments with default encoding."""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="ignore")
    s = str(val)
    try:
        # Test if it can be encoded in the default console encoding
        s.encode("ascii", errors="strict")
        return s
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Replace non-ASCII characters with safe alternatives
        return s.encode("ascii", errors="replace").decode("ascii")


def format_neon_connection_string(url: str) -> str:
    if not url:
        return url

    scheme_mapping = {
        "postgresql+asyncpg": "postgresql",
        "postgres": "postgresql",
    }

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme
        base_scheme = scheme_mapping.get(scheme, scheme)
        if base_scheme != "postgresql" and base_scheme != "postgres":
            return url

        hostname = parsed.hostname
        new_host = hostname
        if hostname and "neon.tech" in hostname and "-pooler" not in hostname:
            parts = hostname.split(".", 1)
            new_host = f"{parts[0]}-pooler.{parts[1]}" if len(parts) == 2 else f"{hostname}-pooler"

        netloc_parts = []
        if parsed.username:
            user_pass = parsed.username
            if parsed.password is not None:
                user_pass += f":{parsed.password}"
            netloc_parts.append(f"{user_pass}@")
        netloc_parts.append(new_host or "")
        netloc_parts.append(":5432")
        new_netloc = "".join(netloc_parts)

        query_params = dict(parse_qsl(parsed.query))
        query_params["sslmode"] = "require"
        query_params["prepareThreshold"] = "0"
        new_query = urlencode(query_params)

        return urlunparse((
            scheme,
            new_netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
    except Exception as e:
        logger.error(f"Error formatting Neon connection string: {e}")
        return url


def clean_psycopg2_uri(url: str) -> str:
    if not url:
        return url
    try:
        parsed = urlparse(url)
        query_params = dict(parse_qsl(parsed.query))
        query_params.pop("prepareThreshold", None)

        scheme = parsed.scheme
        if scheme == "postgresql+asyncpg":
            scheme = "postgresql"

        new_query = urlencode(query_params)
        return urlunparse((
            scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
    except Exception as e:
        logger.error(f"Error cleaning psycopg2 URI: {e}")
        return url


_raw_uri = (
    os.getenv("NEON_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URL_SYNC")
    or ""
)
if _raw_uri.startswith("sqlite"):
    NEON_URI = ""
else:
    NEON_URI = format_neon_connection_string(_raw_uri)

# Track which backend is active
BACKEND = None  # "pg" or "sqlite"
FALLBACK_DB_PATH = None

# Global Connection Pool
import contextlib
import threading

PG_POOL_LOCK = threading.Lock()
PG_POOL = None
POOL_PID = None


# Subclass standard sqlite3 errors for robust catch matching
class OperationalError(real_sqlite3.OperationalError):
    pass


class IntegrityError(real_sqlite3.IntegrityError):
    pass


class ProgrammingError(real_sqlite3.ProgrammingError):
    pass


class NotSupportedError(real_sqlite3.NotSupportedError):
    pass


class InternalError(real_sqlite3.InternalError):
    pass


def convert_sql(query: str) -> str:
    """Convert SQLite SQL to PostgreSQL-compatible SQL.
    Handles: ? → %s, AUTOINCREMENT → SERIAL, datetime() → PG timestamp ops, PRAGMA → skip,
             INSERT OR IGNORE, and INSERT OR REPLACE.
    """
    result = []
    in_single = False
    in_double = False
    for char in query:
        if char == "'" and not in_double:
            in_single = not in_single
            result.append(char)
        elif char == '"' and not in_single:
            in_double = not in_double
            result.append(char)
        elif char == "?" and not in_single and not in_double:
            result.append("%s")
        else:
            result.append(char)

    sql = "".join(result)

    # 1. Handle INSERT OR REPLACE
    if "INSERT OR REPLACE" in sql.upper():
        match = re.search(
            r"INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*(?:VALUES|SELECT)\s*(.*)",
            sql,
            re.IGNORECASE,
        )
        if match:
            table_name = match.group(1)
            columns_str = match.group(2)
            rest_str = match.group(3).strip().rstrip(";")

            columns = [c.strip() for c in columns_str.split(",")]
            if columns:
                key_col = columns[0]
                update_cols = columns[1:]
                update_clauses = [f"{col} = EXCLUDED.{col}" for col in update_cols]
                update_clause_str = ", ".join(update_clauses)
                sql = f"INSERT INTO {table_name} ({columns_str}) VALUES {rest_str} ON CONFLICT ({key_col}) DO UPDATE SET {update_clause_str}"
        else:
            sql = re.sub(
                r"\bINSERT\s+OR\s+REPLACE\s+INTO\b",
                "INSERT INTO",
                sql,
                flags=re.IGNORECASE,
            )

    # 2. Handle INSERT OR IGNORE
    if "INSERT OR IGNORE" in sql.upper():
        sql = re.sub(
            r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", sql, flags=re.IGNORECASE
        )
        sql = sql.strip().rstrip(";")
        if "ON CONFLICT" not in sql.upper():
            sql = sql + " ON CONFLICT DO NOTHING"

    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

    # Translate SQLite last_insert_rowid() to PG lastval()
    sql = re.sub(r"\blast_insert_rowid\(\)", "lastval()", sql, flags=re.IGNORECASE)

    # Replace: datetime('now', '...offset...') → NOW() +/- INTERVAL '...offset...'
    def _fix_datetime(m: re.Match[str]) -> str:
        inner = m.group(1)
        parts = [p.strip() for p in inner.split(",")]
        parts = [p.strip("'\"") if "||" not in p else p for p in parts]
        if len(parts) == 1:
            val = parts[0]
            if val.lower() == "now":
                return "NOW()"
            return f"CAST({val} AS TIMESTAMP)"
        col = parts[0]
        if col.lower() == "now":
            col = "NOW()"
        offset = parts[1]

        # Handle SQLite string concatenation inside interval offset (e.g. '+' || ? || ' minutes')
        if "||" in offset:
            clean_offset = offset
            is_negative = False
            if clean_offset.startswith("'+'") or clean_offset.startswith("`+`") or clean_offset.startswith('"+"'):
                clean_offset = re.sub(r"^['\"`]\+['\"`]\s*\|\|", "", clean_offset).strip()
            elif clean_offset.startswith("'-'") or clean_offset.startswith("`-`") or clean_offset.startswith('"-"'):
                clean_offset = re.sub(r"^['\"`]-['\"`]\s*\|\|", "", clean_offset).strip()
                is_negative = True
            op = "-" if is_negative else "+"
            return f"{col} {op} ({clean_offset})::INTERVAL"

        if offset.startswith("+"):
            return f"{col} + INTERVAL '{offset[1:]}'"
        elif offset.startswith("-"):
            return f"{col} - INTERVAL '{offset[1:]}'"
        else:
            return f"{col} + INTERVAL '{offset}'"

    # Handle datetime() function calls
    sql = re.sub(r"datetime\(([^)]+)\)", _fix_datetime, sql, flags=re.IGNORECASE)

    # Translate SQLite strftime to PostgreSQL EXTRACT/TO_CHAR
    def _fix_strftime(m: re.Match[str]) -> str:
        fmt = m.group(1).strip().strip("'\"")
        val = m.group(2).strip().strip("'\"")
        if fmt == "%s":
            if val.lower() == "now":
                return "EXTRACT(EPOCH FROM NOW())"
            else:
                return f"EXTRACT(EPOCH FROM {m.group(2).strip()})"
        return f"TO_CHAR({m.group(2).strip()}, '{fmt}')"

    sql = re.sub(r"strftime\(([^,]+),\s*([^)]+)\)", _fix_strftime, sql, flags=re.IGNORECASE)

    # Now replace standalone DATETIME types with TIMESTAMP
    sql = re.sub(r"\bDATETIME\b", "TIMESTAMP", sql, flags=re.IGNORECASE)

    # Handle CURRENT_TIMESTAMP → NOW() (safe for both, but PG prefers NOW())
    sql = re.sub(r"\bCURRENT_TIMESTAMP\b", "NOW()", sql, flags=re.IGNORECASE)

    if sql.strip().upper().startswith("PRAGMA TABLE_INFO"):
        match = re.search(
            r"PRAGMA\s+table_info\s*\(\s*['\"]?(\w+)['\"]?\s*\)", sql, re.IGNORECASE
        )
        if match:
            table_name = match.group(1)
            return f"SELECT ordinal_position, column_name, data_type, is_nullable, column_default, 0 FROM information_schema.columns WHERE table_name = '{table_name}'"

    if sql.strip().upper().startswith("PRAGMA"):
        return ""
    if "sqlite_master" in sql.lower():
        sql = re.sub(
            r"\bselect\s+name\s+from\s+sqlite_master\s+where\s+type\s*=\s*'table'\b",
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'",
            sql,
            flags=re.IGNORECASE,
        )
        sql = re.sub(
            r"\bsqlite_master\b", "information_schema.tables", sql, flags=re.IGNORECASE
        )

    # Convert LIKE to ILIKE for case-insensitive behavior matching SQLite
    sql = re.sub(r"\bLIKE\b", "ILIKE", sql, flags=re.IGNORECASE)
    return sql


class PgRow:
    """A dict/sqlite3.Row-compatible row wrapper for PostgreSQL results.

    Supports both integer indexing (row[0]) and column name access (row['name']),
    plus .get() method, matching the sqlite3.Row interface.
    """

    def __init__(
        self, cursor: Any, row_tuple: tuple[Any, ...] | list[Any]
    ) -> None:
        self._row = tuple(row_tuple)
        self._columns: list[str] = []
        if cursor and cursor.description:
            self._columns = [col[0] for col in cursor.description]
        self._col_map = {col.lower(): i for i, col in enumerate(self._columns)}

    def __getitem__(self, key: int | slice | str) -> Any:
        if isinstance(key, (int, slice)):
            return self._row[key]
        if isinstance(key, str):
            idx = self._col_map.get(key.lower())
            if idx is not None:
                return self._row[idx]
            raise KeyError(key)
        raise TypeError(
            f"Row indices must be integers or strings, not {type(key).__name__}"
        )

    def __len__(self) -> int:
        return len(self._row)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._row)

    def __repr__(self) -> str:
        return repr(dict(zip(self._columns, self._row, strict=False)))

    def keys(self) -> list[str]:
        return self._columns

    def get(self, key: int | str, default: Any = None) -> Any:
        try:
            return self[key]
        except (KeyError, IndexError, TypeError):
            return default


class PgCursorWrapper:
    def __init__(self, cursor: Any, connection: Any) -> None:
        self.cursor = cursor
        self._connection_ref = weakref.ref(connection)
        self.lastrowid: int | None = None
        self._description: Any | None = None

    @property
    def connection(self) -> Any:
        return self._connection_ref()

    def __enter__(self) -> "PgCursorWrapper":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _wrap_row(self, row_tuple: tuple[Any, ...]) -> Any:
        """Apply row_factory if set, otherwise return a PgRow for compatibility."""
        conn = self.connection
        if conn and conn.row_factory:
            try:
                return conn.row_factory(self.cursor, row_tuple)
            except Exception as e:
                logger.debug(f"Row factory failed ({e}), using PgRow fallback")
                return PgRow(self.cursor, row_tuple)
        return PgRow(self.cursor, row_tuple)

    def execute(
        self,
        query: str,
        params: dict[str, Any] | tuple[Any, ...] | list[Any] | None = None,
    ) -> "PgCursorWrapper":
        pg_query = convert_sql(query)
        if not pg_query:
            return self

        tables_with_id = {
            "users",
            "cv_profiles",
            "campaigns",
            "orders",
            "wallet_transactions",
            "job_applications",
            "job_queue",
            "email_queue",
            "user_prefs",
            "sent_emails",
            "leads",
        }

        is_insert = pg_query.strip().upper().startswith("INSERT")
        table_name = None
        if is_insert:
            m = re.search(
                r"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)", pg_query, re.IGNORECASE
            )
            if m:
                table_name = m.group(1).lower()

        should_return_id = (
            is_insert
            and table_name in tables_with_id
            and "RETURNING" not in pg_query.upper()
        )
        if should_return_id:
            pg_query = pg_query.strip().rstrip(";") + " RETURNING id"

        try:
            if params is not None:
                self.cursor.execute(pg_query, params)
            else:
                self.cursor.execute(pg_query)

            if should_return_id:
                try:
                    row = self.cursor.fetchone()
                    if row:
                        self.lastrowid = row[0]
                except Exception:
                    pass
        except psycopg2.OperationalError as e:
            raise OperationalError(e)
        except psycopg2.IntegrityError as e:
            raise IntegrityError(e)

        return self

    def executemany(
        self, query: str, seq_of_params: Iterable[Any]
    ) -> "PgCursorWrapper":
        pg_query = convert_sql(query)
        try:
            self.cursor.executemany(pg_query, seq_of_params)
        except psycopg2.OperationalError as e:
            raise OperationalError(e)
        except psycopg2.IntegrityError as e:
            raise IntegrityError(e)
        return self

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

    def fetchall(self) -> list[Any]:
        try:
            rows = self.cursor.fetchall()
            return [self._wrap_row(tuple(r)) for r in rows]
        finally:
            with contextlib.suppress(Exception):
                self.cursor.close()

    def fetchmany(self, size: int | None = None) -> list[Any]:
        try:
            rows = self.cursor.fetchmany() if size is None else self.cursor.fetchmany(size)
            if not rows or (size is not None and len(rows) < size):
                with contextlib.suppress(Exception):
                    self.cursor.close()
            return [self._wrap_row(tuple(r)) for r in rows]
        except Exception as e:
            with contextlib.suppress(Exception):
                self.cursor.close()
            raise e

    def close(self) -> None:
        conn = self.connection
        if conn and hasattr(conn, "open_cursors"):
            with contextlib.suppress(ValueError):
                conn.open_cursors.remove(self)
        with contextlib.suppress(Exception):
            self.cursor.close()

    def __iter__(self) -> "PgCursorWrapper":
        return self

    def __next__(self) -> Any:
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()

    @property
    def rowcount(self) -> int:
        return self.cursor.rowcount

    @property
    def description(self) -> Any | None:
        return self.cursor.description


class PgConnectionWrapper:
    def __init__(self):
        global PG_POOL, BACKEND, POOL_PID
        self.row_factory = None
        self._in_transaction = False
        self._last_rowcount = 0
        self.open_cursors = []
        self.conn = None
        current_pid = os.getpid()

        # If PID has changed, clear the inherited pool so we create a fresh one for this worker process
        if PG_POOL is None or current_pid != POOL_PID:
            with PG_POOL_LOCK:
                if PG_POOL is not None and current_pid != POOL_PID:
                    with contextlib.suppress(Exception):
                        PG_POOL.closeall()
                    PG_POOL = None

                if PG_POOL is None:
                    POOL_PID = current_pid
                    try:
                        # Restrict connection limits to prevent exceeding Neon's 10-connection limit
                        min_conn = int(os.getenv("PG_POOL_MIN", "1"))
                        max_conn = int(os.getenv("PG_POOL_MAX", "3"))
                        # Ensure values are strictly bounded to (1, 3)
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
                    except psycopg2.OperationalError as e:
                        raise OperationalError(e)

        import time
        max_retries = 5
        conn_to_cleanup = None
        try:
            for attempt in range(max_retries):
                try:
                    # 1. Connection Recycling: Loop to get a connection from the pool,
                    # discarding any that are older than 280 seconds.
                    while True:
                        conn_to_cleanup = PG_POOL.getconn()
                        now = time.time()

                        if hasattr(conn_to_cleanup, "created_at"):
                            if now - conn_to_cleanup.created_at > 280:
                                logger.info("[DB] Discarding expired connection in PgConnectionWrapper pool (idle > 280s).")
                                PG_POOL.putconn(conn_to_cleanup, close=True)
                                conn_to_cleanup = None
                                continue  # Fetch a different connection
                        else:
                            conn_to_cleanup.created_at = now
                        break

                    # 2. Connection Testing (Pre-ping): Run a lightweight test query
                    try:
                        with conn_to_cleanup.cursor() as test_cur:
                            test_cur.execute("SELECT 1")
                    except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError) as test_err:
                        logger.warning(f"[DB] Connection pre-ping failed: {test_err}. Discarding stale connection.")
                        PG_POOL.putconn(conn_to_cleanup, close=True)
                        conn_to_cleanup = None
                        # Raise error to trigger outer retry block with backoff
                        raise psycopg2.OperationalError("Stale connection pre-ping failed") from test_err

                    conn_to_cleanup.autocommit = True
                    self.conn = conn_to_cleanup
                    conn_to_cleanup = None  # Transfer ownership to self.conn
                    BACKEND = "pg"
                    break
                except psycopg2.OperationalError as e:
                    if conn_to_cleanup is not None:
                        with contextlib.suppress(Exception):
                            PG_POOL.putconn(conn_to_cleanup, close=True)
                        conn_to_cleanup = None
                    if attempt < max_retries - 1:
                        time.sleep(0.1 * (2 ** attempt))
                    else:
                        raise OperationalError(e)
        except Exception:
            if conn_to_cleanup is not None:
                with contextlib.suppress(Exception):
                    PG_POOL.putconn(conn_to_cleanup, close=True)
                conn_to_cleanup = None
            raise

    def execute(
        self,
        query: str,
        params: dict[str, Any] | tuple[Any, ...] | list[Any] | None = None,
    ) -> PgCursorWrapper:
        if query:
            q_upper = query.strip().upper()
            if q_upper.startswith("BEGIN"):
                self._in_transaction = True
            elif q_upper.startswith("COMMIT") or q_upper.startswith("ROLLBACK"):
                self._in_transaction = False

        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur, self)
        self.open_cursors.append(wrapper)
        res = wrapper.execute(query, params)
        self._last_rowcount = res.rowcount if res else 0
        return res

    def executescript(self, script: str) -> PgCursorWrapper:
        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur, self)
        self.open_cursors.append(wrapper)
        res = wrapper.execute(script)
        self._last_rowcount = res.rowcount if res else 0
        return res

    def executemany(self, query: str, seq_of_params: Iterable[Any]) -> PgCursorWrapper:
        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur, self)
        self.open_cursors.append(wrapper)
        res = wrapper.executemany(query, seq_of_params)
        self._last_rowcount = res.rowcount if res else 0
        return res

    @property
    def changes(self) -> int:
        return self._last_rowcount

    def commit(self) -> None:
        try:
            if self.conn:
                if getattr(self.conn, "autocommit", False):
                    if getattr(self, "_in_transaction", False):
                        with self.conn.cursor() as cur:
                            cur.execute("COMMIT")
                        self._in_transaction = False
                else:
                    self.conn.commit()
        except Exception as e:
            logger.debug(f"Commit failed: {e}")

    def rollback(self) -> None:
        try:
            if self.conn:
                if getattr(self.conn, "autocommit", False):
                    if getattr(self, "_in_transaction", False):
                        with self.conn.cursor() as cur:
                            cur.execute("ROLLBACK")
                        self._in_transaction = False
                else:
                    self.conn.rollback()
        except Exception as e:
            logger.debug(f"Rollback failed: {e}")

    def cursor(self) -> PgCursorWrapper:
        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur, self)
        self.open_cursors.append(wrapper)
        return wrapper

    def close(self) -> None:
        global PG_POOL
        for cur in list(self.open_cursors):
            with contextlib.suppress(Exception):
                cur.close()
        self.open_cursors.clear()
        if PG_POOL and self.conn:
            PG_POOL.putconn(self.conn)
            self.conn = None

    def __enter__(self) -> "PgConnectionWrapper":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()


class SqliteConnectionWrapper:
    """SQLite fallback wrapper with same interface as PgConnectionWrapper."""

    def __init__(self, db_path: str | Any) -> None:
        global BACKEND
        try:
            self.conn = real_sqlite3.connect(
                db_path, check_same_thread=False, timeout=30
            )
        except real_sqlite3.DatabaseError as de:
            if "file is not a database" in str(de):
                logger.error(
                    f"[SHIM] SQLite file is not a database. Auto-healing by removing: {db_path}"
                )
                try:
                    if os.path.exists(db_path):
                        os.remove(db_path)
                except Exception:
                    pass
                self.conn = real_sqlite3.connect(
                    db_path, check_same_thread=False, timeout=30
                )
            else:
                raise de
        self.conn.row_factory = DictLikeRow

        # Enable WAL mode dynamically on local/cloud disks for concurrent performance.
        # Keep DELETE mode only on NFS (PythonAnywhere) to prevent locks.
        is_pa = bool(
            os.environ.get("PYTHONANYWHERE_SITE") or
            os.environ.get("PYTHONANYWHERE_DOMAIN")
        )
        if is_pa:
            self.conn.execute("PRAGMA journal_mode=DELETE")
            self.conn.execute("PRAGMA synchronous=FULL")
            logger.info(f"[DB] Connected to SQLite fallback (DELETE journal mode): {_safe_str(db_path)}")
        else:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            logger.info(f"[DB] Connected to SQLite fallback (WAL journal mode): {_safe_str(db_path)}")

        self.conn.execute("PRAGMA cache_size=-16000")  # 16MB cache
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.execute("PRAGMA encoding='UTF-8'")

        BACKEND = "sqlite"

    @staticmethod
    def _translate_for_sqlite(query: str) -> str:
        """Strip/translate PostgreSQL-specific syntax for SQLite compatibility."""
        # 1. ILIKE → LIKE (SQLite LIKE is case-insensitive for ASCII by default)
        query = re.sub(r"\bILIKE\b", "LIKE", query, flags=re.IGNORECASE)

        # 2. Strip PostgreSQL ::type casts (e.g. value::integer → value)
        query = re.sub(r"::\w+", "", query)

        # 3. Strip RETURNING clause (SQLite doesn't support it; use lastrowid instead)
        query = re.sub(r"\bRETURNING\b.*$", "", query, flags=re.IGNORECASE | re.DOTALL).rstrip()

        # 4. ON CONFLICT (col) DO UPDATE SET → INSERT OR REPLACE (simplified fallback)
        # Already handled upstream by convert_sql for PG path; SQLite receives original
        # INSERT OR REPLACE syntax which SQLite understands natively.

        return query

    def execute(
        self,
        query: str,
        params: dict[str, Any] | tuple[Any, ...] | list[Any] | None = None,
    ) -> real_sqlite3.Cursor:
        cur = self.conn.cursor()
        query = self._translate_for_sqlite(query)
        if params is not None:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur

    def executescript(self, script: str) -> real_sqlite3.Cursor:
        self.conn.executescript(script)
        return self.conn.cursor()

    def executemany(
        self, query: str, seq_of_params: Iterable[Any]
    ) -> real_sqlite3.Cursor:
        cur = self.conn.cursor()
        query = self._translate_for_sqlite(query)
        cur.executemany(query, seq_of_params)
        return cur

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()

    def cursor(self) -> real_sqlite3.Cursor:
        return self.conn.cursor()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SqliteConnectionWrapper":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()


def should_use_pg(db_path: str | Any | None) -> bool:
    # If running inside unit tests/pytest, do NOT use PostgreSQL to keep tests isolated
    import sys

    if (
        "unittest" in sys.modules
        or "pytest" in sys.modules
        or any("pytest" in arg or "unittest" in arg for arg in sys.argv)
    ):
        return False
    # FORCE_PG=1 bypasses all checks and forces PostgreSQL mode
    if os.getenv("FORCE_PG") == "1":
        return True
    if not db_path:
        return True
    db_path_str = str(db_path).lower()
    if db_path_str.startswith("postgresql://") or db_path_str.startswith("postgres://") or db_path_str.startswith("postgresql+asyncpg://"):
        return True
    if ":memory:" in db_path_str:
        return False
    if "backup" in db_path_str:
        return False
    if "temp" in db_path_str:
        return False
    # Also check if NEON_URI is configured — if so, prefer PG for any .db file
    if NEON_URI and (
        "jobhunt" in db_path_str
        or "saas" in db_path_str
        or "database" in db_path_str
        or "cv sam" in db_path_str
    ):
        return True
    main_db_indicators = [
        "saas",
        "sam_max",
        "jobhunt",
        "database_v2",
        "database.db",
        "database.sqlite3",
        "leads",
    ]
    return any(indicator in db_path_str for indicator in main_db_indicators)


def connect(
    db_path: str | Any | None = None, **kwargs: Any
) -> PgConnectionWrapper | SqliteConnectionWrapper:
    """Connect to Neon PG with automatic SQLite fallback."""
    global FALLBACK_DB_PATH
    # Only update FALLBACK_DB_PATH if it is not a PostgreSQL URL string
    if db_path and not (isinstance(db_path, str) and (db_path.startswith("postgresql://") or db_path.startswith("postgres://") or db_path.startswith("postgresql+asyncpg://"))):
        FALLBACK_DB_PATH = db_path

    target_db = db_path or FALLBACK_DB_PATH or "jobhunt_saas_v2.db"
    
    # Resolve the proper SQLite database path for fallback.
    sqlite_db = target_db
    if isinstance(sqlite_db, str) and (sqlite_db.startswith("postgresql://") or sqlite_db.startswith("postgres://") or sqlite_db.startswith("postgresql+asyncpg://")):
        sqlite_db = FALLBACK_DB_PATH if (FALLBACK_DB_PATH and not (isinstance(FALLBACK_DB_PATH, str) and (FALLBACK_DB_PATH.startswith("postgresql") or FALLBACK_DB_PATH.startswith("postgres")))) else "jobhunt_saas_v2.db"

    if not should_use_pg(target_db):
        logger.info(f"[DB] Bypassing PG for non-main database: {_safe_str(target_db)}")
        return SqliteConnectionWrapper(sqlite_db)

    if os.getenv("FORCE_SQLITE") == "1":
        logger.info("[DB] FORCE_SQLITE=1, skipping PG")
        return SqliteConnectionWrapper(sqlite_db)

    if not NEON_URI:
        logger.warning("[DB] No PostgreSQL URL set, using SQLite fallback")
        return SqliteConnectionWrapper(sqlite_db)

    try:
        return PgConnectionWrapper()
    except Exception as pg_err:
        logger.error(
            f"[DB] Failed to connect to Neon PG: {pg_err}. Falling back to SQLite."
        )
        return SqliteConnectionWrapper(sqlite_db)


class DictLikeRow(real_sqlite3.Row):
    """Subclass of sqlite3.Row that adds dict-style .get() support."""

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except (KeyError, IndexError, TypeError):
            return default


# Expose standard SQLite3 properties and error types for compatibility
apilevel = "2.0"
threadsafety = 1
paramstyle = "qmark"

Warning = real_sqlite3.Warning
Error = real_sqlite3.Error
InterfaceError = real_sqlite3.InterfaceError
DatabaseError = real_sqlite3.DatabaseError
DataError = real_sqlite3.DataError
OperationalError = OperationalError
IntegrityError = IntegrityError
InternalError = InternalError
ProgrammingError = ProgrammingError
NotSupportedError = NotSupportedError

Row = DictLikeRow
Connection = PgConnectionWrapper


def get_backend() -> str:
    """Returns current database backend: 'pg' or 'sqlite'."""
    return BACKEND or "unknown"


def get_db(max_retries=3):
    from web.app_v2 import get_db as _web_get_db

    return _web_get_db(max_retries)

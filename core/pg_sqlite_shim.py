import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
import os
import logging
import sqlite3 as real_sqlite3

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_URL") or os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_SYNC") or ""
if NEON_URI.startswith("postgresql+asyncpg://"):
    NEON_URI = NEON_URI.replace("postgresql+asyncpg://", "postgresql://", 1)

# Track which backend is active
BACKEND = None  # "pg" or "sqlite"
FALLBACK_DB_PATH = None

# Global Connection Pool
PG_POOL = None

class OperationalError(Exception):
    pass

class IntegrityError(Exception):
    pass

import re

def convert_sql(query):
    """Convert SQLite SQL to PostgreSQL-compatible SQL.
    Handles: ? → %s, AUTOINCREMENT → SERIAL, datetime() → PG timestamp ops, PRAGMA → skip.
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
        elif char == '?' and not in_single and not in_double:
            result.append('%s')
        else:
            result.append(char)
            
    sql = "".join(result)
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    # Replace: datetime('now', '...offset...') → NOW() +/- INTERVAL '...offset...'
    def _fix_datetime(m):
        inner = m.group(1)
        parts = [p.strip().strip("'\"") for p in inner.split(',')]
        if len(parts) == 1:
            return "NOW()"
        col = parts[0]
        if col.lower() == 'now':
            col = "NOW()"
        offset = parts[1]
        if offset.startswith('+'):
            return f"{col} + INTERVAL '{offset[1:]}'"
        elif offset.startswith('-'):
            return f"{col} - INTERVAL '{offset[1:]}'"
        else:
            return f"{col} + INTERVAL '{offset}'"
    
    # Handle datetime() function calls
    sql = re.sub(r"datetime\(([^)]+)\)", _fix_datetime, sql, flags=re.IGNORECASE)
    
    # Now replace standalone DATETIME types with TIMESTAMP
    sql = re.sub(r"\bDATETIME\b", "TIMESTAMP", sql, flags=re.IGNORECASE)
    
    # Handle CURRENT_TIMESTAMP → NOW() (safe for both, but PG prefers NOW())
    sql = re.sub(r"\bCURRENT_TIMESTAMP\b", "NOW()", sql, flags=re.IGNORECASE)
    
    if sql.strip().upper().startswith("PRAGMA TABLE_INFO"):
        match = re.search(r"PRAGMA\s+table_info\s*\(\s*['\"]?(\w+)['\"]?\s*\)", sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            return f"SELECT ordinal_position, column_name, data_type, is_nullable, column_default, 0 FROM information_schema.columns WHERE table_name = '{table_name}'"
            
    if sql.strip().upper().startswith("PRAGMA"):
        return ""
    # Convert LIKE to ILIKE for case-insensitive behavior matching SQLite
    sql = re.sub(r"\bLIKE\b", "ILIKE", sql, flags=re.IGNORECASE)
    return sql

class PgCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
        
    def execute(self, query, params=None):
        pg_query = convert_sql(query)
        if not pg_query:
            return self
            
        try:
            if params is not None:
                self.cursor.execute(pg_query, params)
            else:
                self.cursor.execute(pg_query)
        except psycopg2.OperationalError as e:
            raise OperationalError(e)
        except psycopg2.IntegrityError as e:
            raise IntegrityError(e)
            
        return self

    def executemany(self, query, seq_of_params):
        pg_query = convert_sql(query)
        try:
            self.cursor.executemany(pg_query, seq_of_params)
        except psycopg2.OperationalError as e:
            raise OperationalError(e)
        except psycopg2.IntegrityError as e:
            raise IntegrityError(e)
        return self
        
    def fetchone(self):
        try:
            res = self.cursor.fetchone()
            if res is None:
                try:
                    self.cursor.close()
                except:
                    pass
            return res
        except Exception as e:
            try:
                self.cursor.close()
            except:
                pass
            raise e
        
    def fetchall(self):
        try:
            return self.cursor.fetchall()
        finally:
            try:
                self.cursor.close()
            except:
                pass
        
    def fetchmany(self, size=None):
        try:
            if size is None:
                res = self.cursor.fetchmany()
            else:
                res = self.cursor.fetchmany(size)
            if not res or (size is not None and len(res) < size):
                try:
                    self.cursor.close()
                except:
                    pass
            return res
        except Exception as e:
            try:
                self.cursor.close()
            except:
                pass
            raise e
        
    def close(self):
        try:
            self.cursor.close()
        except:
            pass

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    def __del__(self):
        try:
            self.cursor.close()
        except:
            pass

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def description(self):
        return self.cursor.description

class PgConnectionWrapper:
    def __init__(self):
        global PG_POOL, BACKEND
        self.row_factory = None
        if PG_POOL is None:
            try:
                PG_POOL = pool.ThreadedConnectionPool(1, 30, NEON_URI, cursor_factory=DictCursor, connect_timeout=5)
            except psycopg2.OperationalError as e:
                raise OperationalError(e)
        
        try:
            self.conn = PG_POOL.getconn()
            self.conn.autocommit = True
            BACKEND = "pg"
        except psycopg2.OperationalError as e:
            raise OperationalError(e)
            
    def execute(self, query, params=None):
        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur)
        return wrapper.execute(query, params)
        
    def executescript(self, script):
        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur)
        return wrapper.execute(script)

    def executemany(self, query, seq_of_params):
        cur = self.conn.cursor()
        wrapper = PgCursorWrapper(cur)
        return wrapper.executemany(query, seq_of_params)
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()

    def cursor(self):
        cur = self.conn.cursor()
        return PgCursorWrapper(cur)
        
    def close(self):
        global PG_POOL
        if PG_POOL and self.conn:
            PG_POOL.putconn(self.conn)
            self.conn = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

class SqliteConnectionWrapper:
    """SQLite fallback wrapper with same interface as PgConnectionWrapper."""
    def __init__(self, db_path):
        global BACKEND
        self.conn = real_sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = real_sqlite3.Row
        
        # Performance tuning for extreme scalability on SQLite
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000") # 64MB cache
        self.conn.execute("PRAGMA busy_timeout=30000")
        
        BACKEND = "sqlite"
        logger.info(f"[DB] Connected to SQLite fallback: {db_path}")
        
    def execute(self, query, params=None):
        cur = self.conn.cursor()
        if params is not None:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur
        
    def executescript(self, script):
        self.conn.executescript(script)
        return self.conn.cursor()

    def executemany(self, query, seq_of_params):
        cur = self.conn.cursor()
        cur.executemany(query, seq_of_params)
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()

    def cursor(self):
        return self.conn.cursor()
        
    def close(self):
        self.conn.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

def connect(db_path=None, **kwargs):
    """Connect to Neon PG with automatic SQLite fallback on PA."""
    global FALLBACK_DB_PATH
    if db_path:
        FALLBACK_DB_PATH = db_path
    
    if os.getenv("FORCE_SQLITE") == "1":
        logger.info("[DB] FORCE_SQLITE=1, skipping PG")
        if FALLBACK_DB_PATH:
            return SqliteConnectionWrapper(FALLBACK_DB_PATH)
        if db_path:
            return SqliteConnectionWrapper(db_path)
        return SqliteConnectionWrapper("jobhunt_saas_v2.db")

    if not NEON_URI:
        logger.warning("[DB] No PostgreSQL URL set, using SQLite fallback")
        if FALLBACK_DB_PATH:
            return SqliteConnectionWrapper(FALLBACK_DB_PATH)
        if db_path:
            return SqliteConnectionWrapper(db_path)
        return SqliteConnectionWrapper("jobhunt_saas_v2.db")

    try:
        return PgConnectionWrapper()
    except Exception as pg_err:
        logger.error(f"[DB] Failed to connect to Neon PG: {pg_err}. Falling back to SQLite.")
        if FALLBACK_DB_PATH:
            return SqliteConnectionWrapper(FALLBACK_DB_PATH)
        if db_path:
            return SqliteConnectionWrapper(db_path)
        return SqliteConnectionWrapper("jobhunt_saas_v2.db")

# Expose standard SQLite3 properties and error types for compatibility
Error = real_sqlite3.Error
DatabaseError = real_sqlite3.DatabaseError
InterfaceError = real_sqlite3.InterfaceError
Row = real_sqlite3.Row
Connection = PgConnectionWrapper

def get_backend():
    """Returns current database backend: 'pg' or 'sqlite'."""
    return BACKEND or "unknown"

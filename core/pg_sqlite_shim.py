import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
import os
import logging
import sqlite3 as real_sqlite3
import sqlite3 as real_sqlite3

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_URL", "postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require")

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
    
    # SQLite datetime('now', offset) → PostgreSQL compatible
    # datetime('now', '-10 minutes') → NOW() - INTERVAL '10 minutes'
    # datetime('now', '+24 hours') → NOW() + INTERVAL '24 hours'
    # datetime('now') → NOW()
    # datetime(started_at, '+24 hours') < datetime('now') → started_at + INTERVAL '24 hours' < NOW()
    
    # Replace: datetime('now', '...offset...') → NOW() +/- INTERVAL '...offset...'
    def _fix_datetime(m):
        inner = m.group(1)
        parts = [p.strip().strip("'\"") for p in inner.split(',')]
        if len(parts) == 1:
            return "NOW()"
        col = parts[0]
        offset = parts[1]
        if offset.startswith('+'):
            return f"{col} + INTERVAL '{offset[1:]}'"
        elif offset.startswith('-'):
            return f"{col} - INTERVAL '{offset[1:]}'"
        else:
            return f"{col} + INTERVAL '{offset}'"
    
    # Handle datetime() function calls
    sql = re.sub(r"datetime\(([^)]+)\)", _fix_datetime, sql, flags=re.IGNORECASE)
    
    # Handle CURRENT_TIMESTAMP → NOW() (safe for both, but PG prefers NOW())
    sql = re.sub(r"\bCURRENT_TIMESTAMP\b", "NOW()", sql, flags=re.IGNORECASE)
    
    if sql.strip().upper().startswith("PRAGMA"):
        return ""
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
        
    def fetchone(self):
        return self.cursor.fetchone()
        
    def fetchall(self):
        return self.cursor.fetchall()
        
    def fetchmany(self, size=None):
        if size is None:
            return self.cursor.fetchmany()
        return self.cursor.fetchmany(size)
        
    def close(self):
        self.cursor.close()

class PgConnectionWrapper:
    def __init__(self):
        global PG_POOL, BACKEND
        if PG_POOL is None:
            try:
                PG_POOL = pool.ThreadedConnectionPool(1, 20, NEON_URI, cursor_factory=DictCursor, connect_timeout=5)
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
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        global PG_POOL
        if PG_POOL and self.conn:
            PG_POOL.putconn(self.conn)
            self.conn = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

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
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

def connect(db_path=None, **kwargs):
    """Connect to Neon PG with automatic SQLite fallback on PA."""
    global FALLBACK_DB_PATH
    if db_path:
        FALLBACK_DB_PATH = db_path
    
    if os.getenv("FORCE_SQLITE") == "1":
        logger.info("[DB] FORCE_SQLITE=1, skipping Neon PG")
        if FALLBACK_DB_PATH and os.path.exists(FALLBACK_DB_PATH):
            return SqliteConnectionWrapper(FALLBACK_DB_PATH)
        elif db_path:
            return SqliteConnectionWrapper(db_path)
    
    try:
        return PgConnectionWrapper()
    except OperationalError:
        logger.warning("[DB] Neon PG unreachable (PA free tier?), falling back to SQLite")
        if FALLBACK_DB_PATH and os.path.exists(FALLBACK_DB_PATH):
            return SqliteConnectionWrapper(FALLBACK_DB_PATH)
        elif db_path:
            return SqliteConnectionWrapper(db_path)
        else:
            raise OperationalError("No database available: PG unreachable and no SQLite path")

class Row:
    pass

def get_backend():
    """Returns current database backend: 'pg' or 'sqlite'."""
    return BACKEND or "unknown"

import psycopg2
from psycopg2.extras import DictCursor
import os
import logging
import sqlite3 as real_sqlite3

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_URL", "postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require")

# Track which backend is active
BACKEND = None  # "pg" or "sqlite"
FALLBACK_DB_PATH = None

class OperationalError(Exception):
    pass

class IntegrityError(Exception):
    pass

def convert_sql(query):
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
        try:
            self.conn = psycopg2.connect(NEON_URI, cursor_factory=DictCursor, connect_timeout=5)
            self.conn.autocommit = True
            global BACKEND
            BACKEND = "pg"
            logger.info("[DB] Connected to Neon PostgreSQL")
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
        self.conn.close()
        
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
        self.conn = real_sqlite3.connect(db_path)
        self.conn.row_factory = real_sqlite3.Row
        global BACKEND
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

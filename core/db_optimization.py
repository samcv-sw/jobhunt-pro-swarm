# ──────────────────────────────────────────────────────────────────────────────
# db_optimization.py - Database Query Optimization Utilities
# Provides connection pooling, query caching, and performance monitoring
# ──────────────────────────────────────────────────────────────────────────────

import functools
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class QueryCache:
    """Simple in-memory query result cache with TTL."""
    
    def __init__(self, ttl_seconds=300):
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl_seconds:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache a value."""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cached values."""
        self.cache.clear()
        self.timestamps.clear()
    
    def size(self) -> int:
        """Get number of cached items."""
        return len(self.cache)


# Global query cache instance
query_cache = QueryCache(ttl_seconds=300)


def cached_query(ttl_seconds: int = 300):
    """Decorator to cache query results.
    
    Usage:
        @cached_query(ttl_seconds=600)
        def get_user_profile(user_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            query_cache.set(cache_key, result)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


def monitor_query_performance(func: Callable) -> Callable:
    """Decorator to monitor and log query execution time.
    
    Logs warning if query takes longer than threshold.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        threshold = 1.0  # seconds
        if duration > threshold:
            logger.warning(
                f"Slow query detected: {func.__name__} took {duration:.2f}s "
                f"(threshold: {threshold}s)"
            )
        else:
            logger.debug(f"{func.__name__} completed in {duration:.3f}s")
        
        return result
    return wrapper


class ConnectionPool:
    """Simple connection pool to reuse database connections."""
    
    def __init__(self, factory: Callable, max_size: int = 10):
        self.factory = factory
        self.max_size = max_size
        self.pool = []
        self.active = set()
    
    def acquire(self):
        """Get a connection from pool or create new one."""
        if self.pool:
            conn = self.pool.pop()
        else:
            conn = self.factory()
        self.active.add(id(conn))
        return conn
    
    def release(self, conn) -> None:
        """Return connection to pool."""
        self.active.discard(id(conn))
        if len(self.pool) < self.max_size:
            self.pool.append(conn)
        else:
            try:
                conn.close()
            except Exception:
                pass
    
    def clear(self) -> None:
        """Close all pooled connections."""
        for conn in self.pool:
            try:
                conn.close()
            except Exception:
                pass
        self.pool.clear()
        logger.info(f"Cleared connection pool ({self.max_size} max size)")


def batch_insert(conn, table: str, columns: list, rows: list, batch_size: int = 1000):
    """Efficiently insert many rows in batches.
    
    Args:
        conn: Database connection
        table: Table name
        columns: List of column names
        rows: List of value tuples
        batch_size: Number of rows per batch
    
    Returns:
        Total number of rows inserted
    """
    total_inserted = 0
    placeholders = ",".join(["?"] * len(columns))
    column_list = ",".join(columns)
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            conn.executemany(sql, batch)
            total_inserted += len(batch)
            logger.debug(f"Inserted batch of {len(batch)} rows into {table}")
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise
    
    logger.info(f"Total {total_inserted} rows inserted into {table}")
    return total_inserted


def suggest_indexes(conn, table: str) -> list:
    """Suggest missing indexes for a table based on common patterns.
    
    Returns: List of suggested CREATE INDEX statements
    """
    suggestions = []
    
    # Get table info
    try:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
    except Exception:
        return suggestions
    
    # Common fields that should have indexes
    common_index_fields = [
        "user_id", "email", "id", "created_at", "updated_at",
        "status", "type", "tenant_id", "organization_id"
    ]
    
    for field in common_index_fields:
        if field in columns:
            index_name = f"idx_{table}_{field}"
            suggestions.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({field});")
    
    return suggestions


def analyze_table(conn, table: str) -> dict:
    """Analyze table and return statistics."""
    try:
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        size = conn.execute(f"SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size();").fetchone()
        
        return {
            "table": table,
            "row_count": row_count,
            "size_bytes": size[0] if size else 0,
            "indexed": True,
        }
    except Exception as e:
        logger.error(f"Could not analyze table {table}: {e}")
        return {}

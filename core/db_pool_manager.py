"""
Database Connection Pool Manager: Optimize PostgreSQL/SQLite connections
Supports connection pooling, min/max pool sizes, connection reuse
Target: Handle 1000+ concurrent users
"""

from typing import Optional, Dict, Any
from sqlalchemy import create_engine, pool, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DBPoolManager:
    """
    Database connection pool manager
    - Manages min/max connections
    - Connection reuse + lifecycle
    - Auto-reconnect on failure
    - Query performance monitoring
    """

    def __init__(
        self,
        database_url: str,
        min_pool_size: int = 10,
        max_pool_size: int = 100,
        pool_recycle: int = 3600,
        echo_sql: bool = False
    ):
        """
        Initialize database pool
        
        Args:
            database_url: Database connection URL
            min_pool_size: Minimum connections to keep open
            max_pool_size: Maximum connections
            pool_recycle: Recycle connections after N seconds (prevent timeout)
            echo_sql: Log SQL statements
        """
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=pool.QueuePool,
            pool_size=min_pool_size,
            max_overflow=max_pool_size - min_pool_size,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Test connections before use
            echo=echo_sql,
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000"  # 30s statement timeout
            }
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # Set up event listeners
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """Setup connection pool event listeners"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Enable pragma settings for SQLite"""
            if "sqlite" in str(self.engine.url):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        @event.listens_for(self.engine, "pool_connect")
        def receive_pool_connect(dbapi_conn, connection_record):
            """Log pool connections"""
            logger.debug(f"Pool connection created: {id(dbapi_conn)}")
        
        @event.listens_for(self.engine, "pool_detach")
        def receive_pool_detach(dbapi_conn, connection_record):
            """Log pool disconnections"""
            logger.debug(f"Pool connection detached: {id(dbapi_conn)}")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session from pool
        Usage: with pool_manager.get_session() as session:
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    async def get_session_async(self) -> Session:
        """Get session (async variant for FastAPI dependencies)"""
        session = self.SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise

    def close_all(self) -> None:
        """Close all connections in pool"""
        self.engine.dispose()
        logger.info("Database pool closed")

    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        if hasattr(self.engine.pool, 'checkedout'):
            checked_out = self.engine.pool.checkedout()
        else:
            checked_out = 0
        
        if hasattr(self.engine.pool, 'size'):
            current_size = self.engine.pool.size()
        else:
            current_size = self.min_pool_size
        
        return {
            "min_size": self.min_pool_size,
            "max_size": self.max_pool_size,
            "current_size": current_size,
            "checked_out": checked_out,
            "available": current_size - checked_out,
            "overflow": (self.max_pool_size - self.min_pool_size) - (current_size - self.min_pool_size)
        }


# Global instances for each database
db_pool_primary = None  # PostgreSQL (production)
db_pool_fallback = None  # SQLite (fallback)


def init_db_pools(
    primary_url: Optional[str] = None,
    fallback_url: Optional[str] = None
) -> None:
    """Initialize global database pools"""
    global db_pool_primary, db_pool_fallback
    
    if primary_url:
        db_pool_primary = DBPoolManager(
            primary_url,
            min_pool_size=10,
            max_pool_size=100
        )
    
    if fallback_url:
        db_pool_fallback = DBPoolManager(
            fallback_url,
            min_pool_size=5,
            max_pool_size=20
        )


def get_db_pool() -> DBPoolManager:
    """Get active database pool (primary or fallback)"""
    if db_pool_primary:
        return db_pool_primary
    elif db_pool_fallback:
        return db_pool_fallback
    else:
        raise RuntimeError("No database pools initialized")


# FastAPI dependency
def get_db_session() -> Session:
    """FastAPI dependency for getting database session"""
    pool = get_db_pool()
    with pool.get_session() as session:
        yield session

import sys
import os
if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim
        sys.modules['sqlite3'] = pg_sqlite_shim
    except Exception:
        pass

try:
    import asyncpg
    ASYNC_PG_AVAILABLE = True
except ImportError:
    ASYNC_PG_AVAILABLE = False

import asyncio
import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_SYNC") or os.getenv("NEON_URL") or ""
if NEON_URI.startswith("postgresql+asyncpg://"):
    NEON_URI = NEON_URI.replace("postgresql+asyncpg://", "postgresql://", 1)

class DatabaseManager:
    def __init__(self) -> None:
        self.pool = None

    async def connect(self) -> None:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url.startswith("libsql://") or db_url.startswith("https://"):
            logger.info("🚀 INFINITE SWARM: Connected to Turso Edge Database (Global Replication)")
            try:
                import libsql_experimental as libsql
                self.pool = libsql.connect(db_url, auth_token=os.getenv("TURSO_AUTH_TOKEN", ""))
            except ImportError:
                logger.warning("libsql_experimental not found. Falling back to HTTP driver.")
                self.pool = None # Handled via HTTP/libsql client in edge mode
            return
            
        try:
            self.pool = await asyncpg.create_pool(dsn=NEON_URI, min_size=1, max_size=20)
            logger.info("Successfully connected to Neon.tech PostgreSQL")
            await self.init_db()
        except Exception as e:
            logger.error(f"Failed to connect to Neon.tech: {e}")

    async def init_db(self) -> None:
        async with self.pool.acquire() as conn:
            # Users table (updated for Viral Growth)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT,
                    phone TEXT,
                    company_name TEXT,
                    user_type TEXT DEFAULT 'jobseeker',
                    api_key TEXT,
                    tokens INTEGER DEFAULT 10,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    stripe_customer_id TEXT,
                    subscription_status TEXT DEFAULT 'free',
                    subscription_end_date TIMESTAMP,
                    squad_id TEXT,
                    referral_code TEXT UNIQUE
                )
            """)
            # Viral Job Squads Table (China Pinduoduo Model)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS job_squads (
                    squad_id TEXT PRIMARY KEY,
                    owner_id TEXT REFERENCES users(user_id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    member_count INTEGER DEFAULT 1,
                    is_complete BOOLEAN DEFAULT FALSE
                )
            """)
            # Jobs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    url TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    salary_range TEXT,
                    posted_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Applications table (Queue)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT REFERENCES users(user_id),
                    job_id TEXT REFERENCES jobs(job_id),
                    status TEXT DEFAULT 'pending',
                    ai_cover_letter TEXT,
                    email_sent_to TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_log TEXT,
                    retry_count INTEGER DEFAULT 0,
                    locked_at TIMESTAMP
                )
            """)
            # Hive Mind Memory (Silicon Valley Trick)
            try:
                await conn.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP;")
                await conn.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                await conn.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
            except Exception as e:
                logger.info(f"ALTER TABLE applications skipped (already exists or error): {e}")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS swarm_intelligence (
                    id SERIAL PRIMARY KEY,
                    company TEXT NOT NULL,
                    successful_keywords TEXT NOT NULL,
                    interview_rate FLOAT DEFAULT 0.0,
                    last_success TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add PostgreSQL indexes for optimized queries
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);")
            logger.info("PostgreSQL schema initialized successfully.")

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from Neon.tech PostgreSQL")

db = DatabaseManager()

# ==============================================================================
# LEGACY DATABASE WRAPPER FOR ORCHESTRATOR COMPATIBILITY
# ==============================================================================
import sqlite3 as sqlite3_sync
import asyncio
import pathlib
import sys

class Database:
    """Legacy async wrapper for SQLite jobs table used by orchestrator."""

    def __init__(self) -> None:
        base_dir = pathlib.Path(__file__).resolve().parent.parent
        try:
            import config
            db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
            self.db_path = str(base_dir / db_name)
        except ImportError:
            self.db_path = str(base_dir / "jobhunt_saas_v2.db")

    def _get_conn(self) -> sqlite3_sync.Connection:
        conn = sqlite3_sync.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3_sync.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=3000000000")
        except Exception: pass
        return conn

    async def save_job(self, job: Dict[str, Any]) -> bool:
        def _save():
            with self._get_conn() as conn:
                try:
                    # Check if user_id column exists
                    has_user_id = True
                    try:
                        conn.execute("SELECT user_id FROM jobs LIMIT 1")
                    except Exception:
                        has_user_id = False

                    if has_user_id:
                        conn.execute("""
                            INSERT INTO jobs 
                            (job_id, user_id, title, company, location, url, snippet, source, salary, status, created_at, email) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                        """, (
                            job.get("job_id"),
                            job.get("user_id"),
                            job.get("title", "Unknown"),
                            job.get("company", "Unknown"),
                            job.get("location", ""),
                            job.get("url", ""),
                            job.get("description", "")[:1000],
                            job.get("source", ""),
                            job.get("salary_range", ""),
                            "new",
                            job.get("email", "")
                        ))
                    else:
                        conn.execute("""
                            INSERT INTO jobs 
                            (job_id, title, company, location, url, snippet, source, salary, status, created_at, email) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                        """, (
                            job.get("job_id"),
                            job.get("title", "Unknown"),
                            job.get("company", "Unknown"),
                            job.get("location", ""),
                            job.get("url", ""),
                            job.get("description", "")[:1000],
                            job.get("source", ""),
                            job.get("salary_range", ""),
                            "new",
                            job.get("email", "")
                        ))
                    conn.commit()
                    return True
                except sqlite3_sync.IntegrityError:
                    return False
        return await asyncio.to_thread(_save)

    async def update_job_status(self, job_id: str, status: str, reason: Optional[str] = None) -> None:
        def _update():
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE jobs SET status=?, response_type=?, updated_at=datetime('now') WHERE job_id=?", 
                    (status, str(reason) if reason else None, job_id)
                )
                conn.commit()
        await asyncio.to_thread(_update)

    async def get_jobs_by_status(self, status: str, limit: int) -> List[Dict[str, Any]]:
        def _get():
            with self._get_conn() as conn:
                cur = conn.execute("SELECT * FROM jobs WHERE status=? LIMIT ?", (status, limit))
                return [dict(r) for r in cur.fetchall()]
        return await asyncio.to_thread(_get)

    async def reset_failed_jobs(self, limit: int) -> int:
        def _reset():
            with self._get_conn() as conn:
                cur = conn.execute(
                    "UPDATE jobs SET status='new' WHERE rowid IN (SELECT rowid FROM jobs WHERE status='failed' LIMIT ?)", 
                    (limit,)
                )
                conn.commit()
                return cur.rowcount
        return await asyncio.to_thread(_reset)

    async def get_jobs_needing_followup(self, followup_level: int) -> List[Dict[str, Any]]:
        def _get():
            with self._get_conn() as conn:
                cur = conn.execute("SELECT * FROM jobs WHERE status='applied' LIMIT 10")
                return [dict(r) for r in cur.fetchall()]
        return await asyncio.to_thread(_get)

    async def mark_followed_up(self, job_id: str, level: int) -> None:
        def _mark():
            with self._get_conn() as conn:
                conn.execute("UPDATE jobs SET status='followed_up' WHERE job_id=?", (job_id,))
                conn.commit()
        await asyncio.to_thread(_mark)

    async def get_stats(self) -> Dict[str, int]:
        def _stats():
            with self._get_conn() as conn:
                try:
                    res = {status: 0 for status in ['new', 'applied', 'failed', 'skipped', 'followed_up']}
                    cur = conn.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
                    total = 0
                    for row in cur.fetchall():
                        status = row[0]
                        count = row[1]
                        if status in res:
                            res[status] = count
                        total += count
                    res["total"] = total
                    return res
                except sqlite3_sync.OperationalError:
                    return {"total": 0, "new": 0, "applied": 0, "failed": 0, "skipped": 0, "followed_up": 0}
        return await asyncio.to_thread(_stats)

    async def create_tables(self) -> None:
        def _create():
            with self._get_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        job_id VARCHAR(64) UNIQUE NOT NULL,
                        user_id VARCHAR(64),
                        company VARCHAR(255) NOT NULL, 
                        title VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL, 
                        location VARCHAR(255),
                        salary VARCHAR(100), 
                        url TEXT, 
                        source VARCHAR(50),
                        snippet TEXT, 
                        status VARCHAR(50) NOT NULL,
                        match_score NUMERIC(5, 2), 
                        response_type VARCHAR(50),
                        applied_at VARCHAR(50), 
                        responded_at VARCHAR(50),
                        created_at DATETIME, 
                        updated_at DATETIME
                    )
                """)
                # Automated migration: add user_id column to existing SQLite jobs tables if it doesn't exist
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN user_id VARCHAR(64)")
                except Exception:
                    pass
                # Add indexes for optimized job lookups
                try:
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_sqlite_jobs_status ON jobs(status)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_sqlite_jobs_user_id ON jobs(user_id)")
                except Exception:
                    pass
                conn.commit()
        await asyncio.to_thread(_create)

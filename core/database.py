try:
    import asyncpg
    ASYNC_PG_AVAILABLE = True
except ImportError:
    ASYNC_PG_AVAILABLE = False

import asyncio
import os
import logging

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_SYNC") or ""

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        db_url = os.getenv("DATABASE_URL", "")
        if db_url.startswith("libsql://"):
            logger.info("PROJECT APEX: Connected to Turso Edge Database (Global Replication)")
            self.pool = None # Handled via HTTP/libsql client in edge mode
            # Initialize schema via edge
            return
            
        try:
            self.pool = await asyncpg.create_pool(dsn=NEON_URI, min_size=1, max_size=20)
            logger.info("Successfully connected to Neon.tech PostgreSQL")
            await self.init_db()
        except Exception as e:
            logger.error(f"Failed to connect to Neon.tech: {e}")

    async def init_db(self):
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
            logger.info("PostgreSQL schema initialized successfully.")

    async def disconnect(self):
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
    def __init__(self):
        # Resolve to jobhunt_saas_v2.db in root dir
        base_dir = pathlib.Path(__file__).resolve().parent.parent
        self.db_path = str(base_dir / "jobhunt_saas_v2.db")
        try:
            import config
            db_path_val = getattr(config, "DB_PATH", None)
            if db_path_val is not None:
                self.db_path = str(base_dir / db_path_val)
        except ImportError:
            pass

    def _get_conn(self):
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

    async def save_job(self, job):
        def _save():
            with self._get_conn() as conn:
                try:
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

    async def update_job_status(self, job_id, status, reason=None):
        def _update():
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE jobs SET status=?, response_type=?, updated_at=datetime('now') WHERE job_id=?", 
                    (status, str(reason) if reason else None, job_id)
                )
                conn.commit()
        await asyncio.to_thread(_update)

    async def get_jobs_by_status(self, status, limit):
        def _get():
            with self._get_conn() as conn:
                cur = conn.execute("SELECT * FROM jobs WHERE status=? LIMIT ?", (status, limit))
                return [dict(r) for r in cur.fetchall()]
        return await asyncio.to_thread(_get)

    async def reset_failed_jobs(self, limit):
        def _reset():
            with self._get_conn() as conn:
                cur = conn.execute(
                    "UPDATE jobs SET status='new' WHERE rowid IN (SELECT rowid FROM jobs WHERE status='failed' LIMIT ?)", 
                    (limit,)
                )
                conn.commit()
                return cur.rowcount
        return await asyncio.to_thread(_reset)

    async def get_jobs_needing_followup(self, followup_level):
        def _get():
            with self._get_conn() as conn:
                cur = conn.execute("SELECT * FROM jobs WHERE status='applied' LIMIT 10")
                return [dict(r) for r in cur.fetchall()]
        return await asyncio.to_thread(_get)

    async def mark_followed_up(self, job_id, level):
        def _mark():
            with self._get_conn() as conn:
                conn.execute("UPDATE jobs SET status='followed_up' WHERE job_id=?", (job_id,))
                conn.commit()
        await asyncio.to_thread(_mark)

    async def create_tables(self):
        pass

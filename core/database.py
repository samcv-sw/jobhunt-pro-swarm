import asyncpg
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

NEON_URI = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_SYNC") or ""

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
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

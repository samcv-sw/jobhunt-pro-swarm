import asyncio
import logging

logger = logging.getLogger(__name__)
import os
import sqlite3
import sys

# Add project root to sys.path
sys.path.insert(0, r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi")

# Set up test database path
temp_db_path = "test_scratch.db"
os.environ["DB_PATH"] = temp_db_path
os.environ["FORCE_SQLITE"] = "1"

# Create schema
def init_db():
    conn = sqlite3.connect(temp_db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            phone TEXT,
            company_name TEXT,
            user_type TEXT DEFAULT 'jobseeker',
            wallet_balance REAL DEFAULT 0,
            total_spent REAL DEFAULT 0,
            api_key TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            byo_smtp_email TEXT,
            byo_smtp_token TEXT,
            oauth_provider TEXT,
            oauth_access_token TEXT,
            oauth_refresh_token TEXT,
            oauth_expires_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cv_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            profile_name TEXT,
            cv_text TEXT,
            cover_letter_template TEXT,
            email_template TEXT,
            skills TEXT,
            experience_years INTEGER,
            target_titles TEXT,
            target_locations TEXT,
            home_country TEXT DEFAULT 'Lebanon',
            min_local_salary REAL DEFAULT 0,
            min_international_salary REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            profile_id INTEGER,
            status TEXT DEFAULT 'pending',
            total_companies INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            open_count INTEGER DEFAULT 0,
            response_count INTEGER DEFAULT 0,
            bouquets TEXT,
            engine_type TEXT DEFAULT 'cloud',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Seed state
tenant_id = "user_tenant_camp"
campaign_id = "camp_123"
conn = sqlite3.connect(temp_db_path)
conn.execute("INSERT INTO users (user_id, email, password_hash, name) VALUES (?, ?, 'hash', 'Camp User')", (tenant_id, "camp_user@domain.com"))
conn.execute("INSERT INTO cv_profiles (user_id, skills, experience_years, target_titles) VALUES (?, 'BGP, Cisco', 10, 'Network Engineer')", (tenant_id,))
conn.execute("INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, status, total_companies) VALUES (?, ?, 'order_123', 1, 'pending', 10)", (campaign_id, tenant_id))
conn.commit()
conn.close()

os.environ["TENANT_USER_TENANT_CAMP_SMTP_USER"] = "camp_smtp@domain.com"
os.environ["TENANT_USER_TENANT_CAMP_SMTP_PASS"] = "camp_pass"

import config as config_mod
from core.campaign_runner import run_campaign


def get_db_fn():
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    return conn

async def test():
    try:
        res = await run_campaign(campaign_id, get_db_fn, config_mod)
        logger.info("Result:", res)
    except Exception as e:
        logger.info("Error during campaign run:", e)
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

asyncio.run(test())

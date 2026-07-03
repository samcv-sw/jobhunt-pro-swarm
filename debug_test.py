import os
import sys
import sqlite3
import tempfile
import uuid
import asyncio
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class StopCampaignException(BaseException):
    pass

async def debug():
    temp_db_path = os.path.join(tempfile.gettempdir(), f"debug_tenant_smtp_{uuid.uuid4().hex}.db")
    os.environ["DB_PATH"] = temp_db_path
    os.environ["FORCE_SQLITE"] = "1"

    # Create tables
    with sqlite3.connect(temp_db_path) as conn:
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
                is_active INTEGER DEFAULT 1
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                order_type TEXT NOT NULL,
                package_name TEXT,
                company_count INTEGER,
                amount_usd REAL NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed data
        tenant_id = "user_tenant_camp"
        campaign_id = "camp_123"
        conn.execute(
            "INSERT INTO users (user_id, email, password_hash, name) VALUES (?, ?, 'hash', 'Camp User')",
            (tenant_id, "camp_user@domain.com")
        )
        conn.execute(
            "INSERT INTO cv_profiles (user_id, skills, experience_years, target_titles) VALUES (?, 'BGP, Cisco', 10, 'Network Engineer')",
            (tenant_id,)
        )
        conn.execute(
            "INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, status, total_companies) VALUES (?, ?, 'order_123', 1, 'pending', 10)",
            (campaign_id, tenant_id)
        )
        conn.commit()

    os.environ["TENANT_USER_TENANT_CAMP_SMTP_USER"] = "camp_smtp@domain.com"
    os.environ["TENANT_USER_TENANT_CAMP_SMTP_PASS"] = "camp_pass"

    from core.campaign_runner import run_campaign
    import config as config_mod

    # Setup logger mock/spy
    import logging
    logger = logging.getLogger("core.campaign_runner")
    
    # We won't patch the logger, we will add a handler to print or inspect logs!
    class TestHandler(logging.Handler):
        def emit(self, record):
            print(f"LOG [{record.levelname}]: {record.getMessage()}")
            if "Loaded tenant-specific SMTP credentials" in record.getMessage():
                raise StopCampaignException("STOP")

    handler = TestHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    def get_db_fn():
        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    try:
        res = await run_campaign(campaign_id, get_db_fn, config_mod)
        print("Result:", res)
    except StopCampaignException:
        print("Success: StopCampaignException raised!")
    except Exception as e:
        print("Failed with Exception:", e)
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

asyncio.run(debug())

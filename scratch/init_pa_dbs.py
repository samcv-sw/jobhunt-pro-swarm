import sys
import os
import asyncio
import sqlite3

# Ensure data directory exists
os.makedirs('/home/JHFGUF/jobhunt/data', exist_ok=True)

# Overwrite DATABASE_URL in environment before importing core.database
# to force SQLAlchemy to initialize the SQLite database engine.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db"

# Add project root to path
sys.path.insert(0, '/home/JHFGUF/jobhunt')

from core.database import Base, engine
from web.app_v2 import init_saas_v2_db, db_path

async def main():
    print("Creating tables in backend SQLite database (forcing sqlite+aiosqlite)...")
    # Initialize the backend database tables (used by routers/REST APIs)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Backend SQLite database tables initialized successfully!")

    print(f"Creating tables in web frontend SQLite database at {db_path}...")
    # Initialize the frontend webapp database tables (used by templates/public routes)
    init_saas_v2_db()
    print("Web frontend SQLite database tables initialized successfully!")

if __name__ == '__main__':
    asyncio.run(main())

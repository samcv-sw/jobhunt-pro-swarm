import sys
import os
import asyncio
import sqlite3

# Add project root to path
sys.path.insert(0, '/home/JHFGUF/jobhunt')

from core.database import Base, engine
from web.app_v2 import init_saas_v2_db, db_path

async def main():
    print(f"Creating tables in backend SQLite database...")
    # Ensure data directory exists
    os.makedirs('/home/JHFGUF/jobhunt/data', exist_ok=True)
    
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

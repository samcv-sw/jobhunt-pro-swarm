import sys
import os
import asyncio
import sqlite3

db_paths = [
    "/home/JHFGUF/data/jobhunt_saas_v2.db",
    "/home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db",
    "/home/JHFGUF/jobhunt_saas_v2.db",
    "/home/JHFGUF/jobhunt/jobhunt_saas_v2.db"
]

# Ensure project root in path
sys.path.insert(0, '/home/JHFGUF/jobhunt')
from core.database import Base

async def init_backend_db(db_path):
    print(f"Initializing backend tables in: {db_path}")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print(f"Backend tables initialized in: {db_path}")

def init_frontend_db(db_path):
    print(f"Initializing frontend tables in: {db_path}")
    import web.app_v2
    # Overwrite database path in web.app_v2 dynamically
    web.app_v2.db_path = db_path
    web.app_v2.init_saas_v2_db()
    print(f"Frontend tables initialized in: {db_path}")

async def main():
    for path in db_paths:
        try:
            await init_backend_db(path)
        except Exception as e:
            print(f"Error seeding backend for {path}: {e}")
        try:
            init_frontend_db(path)
        except Exception as e:
            print(f"Error seeding frontend for {path}: {e}")

if __name__ == '__main__':
    asyncio.run(main())

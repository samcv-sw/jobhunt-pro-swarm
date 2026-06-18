import traceback, asyncio, os
os.environ['DB_PATH'] = 'pa_jobhunt_saas_v2.db'
from core.campaign_runner import run_campaign
import sqlite3
def local_get_db():
    c = sqlite3.connect('pa_jobhunt_saas_v2.db')
    c.row_factory = sqlite3.Row
    return c
import config

async def main():
    try:
        res = await run_campaign('camp_33fde9c9dcea4115', local_get_db, config)
        print("Result:", res)
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())

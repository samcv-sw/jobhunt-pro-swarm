"""
Telegram Bot Runner — standalone process for PythonAnywhere
Runs independently from the web app via polling.
"""
import os
import sys
if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim
        sys.modules['sqlite3'] = pg_sqlite_shim
    except Exception:
        pass

sys.path.insert(0, '/home/JHFGUF/jobhunt')
sys.path.insert(0, '/home/JHFGUF/jobhunt/web')

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv('/home/JHFGUF/jobhunt/.env')
except Exception:
    pass

import asyncio
from core.telegram_bot import TelegramBot

async def main():
    bot = TelegramBot()
    if not bot.enabled:
        print("ERROR: Bot not enabled - check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return
    print(f"Bot enabled. Token: {bot.token[:10]}..., Chat: {bot.chat_id}")
    print("Starting polling loop...")
    await bot.run_bot()

if __name__ == '__main__':
    asyncio.run(main())

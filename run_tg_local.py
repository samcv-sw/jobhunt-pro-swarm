"""Run the Telegram bot locally (Windows) — independent of PA uWSGI."""
import os, sys
PROJ = r"C:\Users\samde\Desktop\cv sam new ma3 kimi"
sys.path.insert(0, PROJ)
sys.path.insert(0, os.path.join(PROJ, 'web'))
os.chdir(PROJ)

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJ, '.env'))
except Exception:
    pass

import asyncio
from core.telegram_bot import start_telegram_bot

async def main():
    print("Starting Telegram Bot (local mode)...")
    await start_telegram_bot()

if __name__ == '__main__':
    asyncio.run(main())

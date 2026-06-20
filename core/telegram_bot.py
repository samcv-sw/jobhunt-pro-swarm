import httpx
import asyncio
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

async def send_telegram_message(message: str):
    """
    Sends a push notification to the configured Telegram chat.
    Fails silently if not configured so it doesn't break the worker.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        await asyncio.sleep(3.5) # ANTI-BAN: Respect Telegram API rate limits (1 msg per 3s)
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=5.0)
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

# Synchronous wrapper if needed by non-async code
def send_telegram_message_sync(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        loop.create_task(send_telegram_message(message))
    else:
        loop.run_until_complete(send_telegram_message(message))

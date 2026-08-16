"""JobHunt Pro — Telegram Webhook Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Telegram"])


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """Handle incoming Telegram webhook updates — resolves bot via app.state or lazy load."""
    bot_instance = getattr(request.app.state, "bot_instance", None)
    if not bot_instance or not getattr(bot_instance, "enabled", False):
        try:
            from core.telegram.bot import TelegramBot
            bot_instance = TelegramBot()
            request.app.state.bot_instance = bot_instance
        except Exception as e:
            logger.error("Failed to lazy load TelegramBot: %s", e)
            return {"status": "error", "detail": f"Bot initialization failed: {e}"}

    if not bot_instance or not getattr(bot_instance, "enabled", False):
        return {"status": "bot_disabled"}

    try:
        update = await request.json()
        logger.info("Received Telegram webhook update")
        await bot_instance.process_webhook_update(update)
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        logger.error("Error handling Telegram webhook update: %s", e)
        return {"status": "error", "detail": str(e)}

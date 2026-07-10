"""
core/telegram_bot.py
JobHunt Pro - Telegram Bot Wrapper
Redirects all imports and variables to core.telegram.bot to avoid code duplication.
"""

from core.telegram.bot import (
    TelegramBot,
    send_telegram_message_sync,
    start_telegram_bot,
)

__all__ = [
    "TelegramBot",
    "send_telegram_message_sync",
    "start_telegram_bot",
]

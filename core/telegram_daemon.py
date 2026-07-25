"""
JobHunt Pro — 24/7 Permanent Self-Healing Telegram Bot Daemon
Ensures 100% cloud permanence, auto-reconnection, stale update purging,
and freeze-proof execution even if idle for days.
"""

import asyncio
import logging
import os
import sys
import time
import threading

# Ensure project root is in sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import datetime
import httpx

import config
from core.telegram.bot import TelegramBot

logger = logging.getLogger("TelegramDaemon")


class TelegramBotDaemon:
    """Self-healing 24/7 daemon supervisor for JobHunt Pro Telegram Bot."""

    def __init__(self):
        self.bot = TelegramBot()
        self.running = False
        self.last_heartbeat = time.time()
        self.restart_count = 0
        self.max_restart_backoff = 30  # seconds

    async def _check_network(self) -> bool:
        """Check internet connectivity to Telegram API."""
        try:
            url = f"https://api.telegram.org/bot{self.bot.token}/getMe"
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                return res.status_code == 200
        except Exception:
            return False

    async def run_forever(self):
        """Main self-healing supervisor loop — runs permanently 24/7."""
        if not self.bot.enabled:
            logger.warning("[Daemon] Telegram Bot token or chat_id not configured. Daemon exiting.")
            return

        self.running = True
        logger.info("🚀 Starting 24/7 Permanent Telegram Bot Daemon...")

        while self.running:
            try:
                # Purge any stale pending updates on startup/reconnect to prevent stall
                logger.info("[Daemon] Purging stale updates & initializing clean state...")
                try:
                    res = await self.bot.http_client.get(
                        f"{self.bot.base_url}/getUpdates?offset=-1&timeout=1"
                    )
                    if res.status_code == 200:
                        updates = res.json().get("result", [])
                        if updates:
                            last_id = updates[-1]["update_id"]
                            await self.bot.http_client.get(
                                f"{self.bot.base_url}/getUpdates?offset={last_id + 1}&timeout=1"
                            )
                except Exception as purge_err:
                    logger.debug(f"[Daemon] Stale update purge notice: {purge_err}")

                # Launch polling bot loop
                logger.info("[Daemon] Launching bot polling engine...")
                self.restart_count = 0
                await self.bot.run_bot()

            except asyncio.CancelledError:
                logger.info("[Daemon] Daemon loop cancelled — shutting down cleanly.")
                self.running = False
                break
            except Exception as e:
                self.restart_count += 1
                backoff = min(self.max_restart_backoff, 2 ** min(self.restart_count, 5))
                logger.error(
                    f"[Daemon] Bot engine crashed: {e}. Auto-restarting in {backoff}s (Attempt #{self.restart_count})..."
                )

                # Verify network before restarting
                network_ok = await self._check_network()
                if not network_ok:
                    logger.warning("[Daemon] Network offline or Telegram API unreachable. Waiting for connection...")
                    while self.running and not await self._check_network():
                        await asyncio.sleep(5)

                await asyncio.sleep(backoff)

    def stop(self):
        """Stop the daemon."""
        self.running = False


_daemon_instance = None
_daemon_thread = None


def start_telegram_daemon_background():
    """Start Telegram Bot Daemon in a dedicated 24/7 background thread."""
    global _daemon_instance, _daemon_thread

    if _daemon_thread and _daemon_thread.is_alive():
        logger.info("[Daemon] Background daemon thread is already running.")
        return _daemon_instance

    def _thread_worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        global _daemon_instance
        _daemon_instance = TelegramBotDaemon()
        try:
            loop.run_until_complete(_daemon_instance.run_forever())
        except Exception as err:
            logger.error(f"[Daemon] Thread worker exception: {err}")
        finally:
            loop.close()

    _daemon_thread = threading.Thread(target=_thread_worker, daemon=True, name="TelegramDaemonThread")
    _daemon_thread.start()
    logger.info("[Daemon] 24/7 Telegram Bot Daemon thread launched successfully.")
    return _daemon_instance


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    daemon = TelegramBotDaemon()
    try:
        asyncio.run(daemon.run_forever())
    except KeyboardInterrupt:
        logger.info("[Daemon] Stopped by user.")

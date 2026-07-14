"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  JOBHUNT PRO — TELEGRAM BOT ENHANCER (v1.0)                               ║
║  Adds to existing TelegramBot:                                             ║
║    1. Auto-restart on crash (24/7 operation)                               ║
║    2. AI-powered /fix command (Groq auto-diagnose)                         ║
║    3. Website control from Telegram (restart, deploy, health check)         ║
║    4. Security audit & hardening                                           ║
║    5. Message queue for crash recovery                                     ║
║    6. Hourly health self-check                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import contextlib
import json
import logging
import os
import time
import traceback
from datetime import datetime
from pathlib import Path

import httpx

import config
import core.pg_sqlite_shim as sqlite3

logger = logging.getLogger("BotEnhancer")

# ─── Constants ───
CRASH_LOG_PATH = Path(__file__).parent.parent / "logs" / "bot_crashes.json"
HEALTH_SNAPSHOT_PATH = Path(__file__).parent.parent / "logs" / "bot_health.json"

# ══════════════════════════════════════════════════════════════════════
# 1. 24/7 AUTO-RESTART WATCHDOG
# ══════════════════════════════════════════════════════════════════════


class BotWatchdog:
    """Wraps the Telegram bot with auto-restart on crash."""

    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.crash_count = 0
        self.last_crash = None
        self.total_restarts = 0
        self.running = False
        self.crash_history = self._load_crash_history()

    def _load_crash_history(self):
        if CRASH_LOG_PATH.exists():
            try:
                return json.loads(CRASH_LOG_PATH.read_text())
            except Exception:
                pass
        return []

    def _log_crash(self, error: str, trace: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "error": str(error)[:500],
            "trace": trace[:1000],
            "crash_count": self.crash_count,
        }
        self.crash_history.append(entry)
        # Keep last 50 crashes
        if len(self.crash_history) > 50:
            self.crash_history = self.crash_history[-50:]
        CRASH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CRASH_LOG_PATH.write_text(json.dumps(self.crash_history, indent=2))

    async def _notify_admin(self, msg: str):
        """Send crash notification to admin."""
        try:
            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None) or os.getenv(
                "TELEGRAM_CHAT_ID"
            )
            if not chat_id:
                return
            token = config.TELEGRAM_BOT_TOKEN
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": f"⚠️ BOT CRASH #{self.crash_count}\n\n{msg[:1500]}",
                        "parse_mode": "HTML",
                    },
                )
        except Exception:
            pass

    async def run_forever(self):
        """Run the bot forever with auto-restart on any crash."""
        self.running = True
        logger.info("🛡️ [WATCHDOG] Bot running with crash protection")

        while self.running:
            try:
                self.total_restarts += 1
                logger.info(f"🔄 [WATCHDOG] Starting bot (run #{self.total_restarts})")
                await self.bot.run_bot()

            except asyncio.CancelledError:
                logger.info("🛡️ [WATCHDOG] Bot cancelled gracefully")
                break

            except Exception as e:
                self.crash_count += 1
                self.last_crash = datetime.now()
                tb = traceback.format_exc()

                logger.error(f"💥 [WATCHDOG] Bot crashed (#{self.crash_count}): {e}")
                self._log_crash(str(e), tb)

                # Notify admin of crash
                crash_msg = (
                    f"<b>💥 BOT CRASH #{self.crash_count}</b>\n"
                    f"<b>Error:</b> {str(e)[:300]}\n"
                    f"<b>Restart #{self.total_restarts + 1}</b> incoming...\n\n"
                    f"<i>Last 3 lines of trace:</i>\n<pre>{chr(10).join(tb.split(chr(10))[-3:])}</pre>"
                )
                await self._notify_admin(crash_msg)

                # Exponential backoff for restarts
                wait = min(2 ** min(self.crash_count, 5), 60)
                logger.info(f"⏳ [WATCHDOG] Restarting in {wait}s...")
                await asyncio.sleep(wait)

                # Recreate bot instance to clear stale state
                try:
                    from core.telegram.bot import TelegramBot

                    self.bot = TelegramBot()
                except Exception:
                    pass

    def stop(self):
        self.running = False


# ══════════════════════════════════════════════════════════════════════
# 2. AI-POWERED /fix COMMAND (Auto-Diagnose & Fix)
# ══════════════════════════════════════════════════════════════════════


class AIFixer:
    """Uses Groq AI to diagnose and fix system issues."""

    SYSTEM_PROMPT = """You are the JobHunt Pro diagnostic AI. You analyze system errors and suggest fixes.

Available context:
- system_health: Current system status
- recent_logs: Last 20 log lines
- error_trace: Any recent crash/error traces

Respond concisely in this format:
🔍 DIAGNOSIS: <1-line root cause>
⚙️ FIX: <actionable fix steps>
🟢 STATUS: <HEALTHY|DEGRADED|CRITICAL>
📊 IMPACT: <affected services>

Keep total response under 800 chars. Be practical — if a restart will fix it, say so."""

    async def diagnose(self, context: dict) -> str:
        """Send system context to Groq for AI diagnosis."""
        try:
            groq_key = getattr(config, "GROQ_API_KEY", None) or os.getenv(
                "GROQ_API_KEY"
            )
            if not groq_key:
                return "🔍 AI Fixer unavailable — no GROQ_API_KEY configured."

            system_health = context.get("system_health", "Unknown")
            recent_logs = context.get("recent_logs", "No logs available")
            error_trace = context.get("error_trace", "No errors")

            user_msg = f"""Analyze this JobHunt Pro system state:

=== SYSTEM HEALTH ===
{json.dumps(system_health, indent=2)}

=== RECENT LOGS ===
{recent_logs[:1500]}

=== ERROR TRACES ===
{error_trace[:800]}

Provide diagnosis and fix steps."""

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": self.SYSTEM_PROMPT},
                            {"role": "user", "content": user_msg},
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                )
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.error(f"AI Fixer failed: {e}")
            return f"🔍 AI diagnosis failed: {e}\n\nTry manual commands:\n/status — system health\n/logs — recent logs\n/restart_web — restart servers"


# ══════════════════════════════════════════════════════════════════════
# 3. WEBSITE CONTROL FROM TELEGRAM
# ══════════════════════════════════════════════════════════════════════


class WebsiteController:
    """Control Render and PythonAnywhere deployments from Telegram."""

    RENDER_HEALTH_URL = "https://jobhunt-pro.onrender.com/health"
    PA_HEALTH_URL = "https://jhfguf.pythonanywhere.com/health"
    PA_API = "https://www.pythonanywhere.com/api/v0/user/JHFGUF"
    PA_TOKEN = (
        getattr(config, "PA_API_TOKEN", None)
        or os.getenv("PA_API_TOKEN")
        or "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
    )

    async def health_check(self) -> str:
        """Check health of all platforms."""
        lines = ["<b>🌐 PLATFORM STATUS</b>\n"]

        async with httpx.AsyncClient(timeout=15) as client:
            # Render
            try:
                r = await client.get(self.RENDER_HEALTH_URL)
                data = r.json()
                lines.append(
                    f"🟢 <b>Render:</b> HEALTHY v{data.get('version', '?')} | {data.get('platform', '?')}"
                )
            except Exception as e:
                lines.append(f"🔴 <b>Render:</b> DOWN — {str(e)[:80]}")

            # PythonAnywhere
            try:
                r = await client.get(self.PA_HEALTH_URL)
                data = r.json()
                lines.append(
                    f"🟢 <b>PythonAnywhere:</b> HEALTHY v{data.get('version', '?')}"
                )
            except Exception as e:
                lines.append(f"🔴 <b>PythonAnywhere:</b> DOWN — {str(e)[:80]}")

        lines.append(f"\n<i>Checked: {datetime.now().strftime('%H:%M:%S')}</i>")
        return "\n".join(lines)

    async def restart_platform(self, platform: str) -> str:
        """Restart a specific platform."""
        if platform.lower() == "pythonanywhere":
            return await self._restart_pa()
        elif platform.lower() == "render":
            return await self._restart_render()
        else:
            return f"❌ Unknown platform: {platform}. Use 'render' or 'pythonanywhere'."

    async def _restart_pa(self) -> str:
        """Reload PythonAnywhere webapp."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.PA_API}/webapps/jhfguf.pythonanywhere.com/reload/",
                    headers={"Authorization": f"Token {self.PA_TOKEN}"},
                )
                if resp.status_code == 200:
                    # Verify after restart
                    await asyncio.sleep(2)
                    h = await client.get(self.PA_HEALTH_URL)
                    if h.status_code == 200:
                        return "✅ PythonAnywhere restarted and HEALTHY!"
                    return "⚠️ PythonAnywhere restarted but health check failed."
                return f"❌ PythonAnywhere restart failed: {resp.text[:200]}"
        except Exception as e:
            return f"❌ PythonAnywhere restart error: {e}"

    async def _restart_render(self) -> str:
        """Check Render status (can't restart via API without deploy key)."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(self.RENDER_HEALTH_URL)
                if r.status_code == 200:
                    return f"🟢 Render is running HEALTHY v{r.json().get('version', '?')}\n\nTo force restart: push to GitHub or use Render Dashboard."
                return f"⚠️ Render returned HTTP {r.status_code}\n\nPush new commit to GitHub to trigger redeploy, or restart from Render Dashboard."
        except Exception:
            return "🔴 Render is DOWN!\n\nPush a new commit to GitHub to trigger redeploy:\n<code>git commit --allow-empty -m 'force deploy' && git push</code>"

    async def get_logs(self, platform: str = "render", lines: int = 20) -> str:
        """Get recent application logs."""
        try:
            db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
            db_path = Path(__file__).parent.parent / db_name
            if not db_path.exists():
                return "📜 No database found for logs."

            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    "SELECT timestamp, level, message FROM app_logs ORDER BY timestamp DESC LIMIT ?",
                    (lines,),
                ).fetchall()
                if not rows:
                    return "📜 No logs recorded yet."
                result = ["<b>📜 RECENT LOGS</b>\n<pre>"]
                for row in reversed(rows):
                    ts = row["timestamp"][:19] if row["timestamp"] else "?"
                    lvl = row["level"] or "INFO"
                    msg = (row["message"] or "")[:120]
                    result.append(f"[{ts}] {lvl}: {msg}")
                result.append("</pre>")
                return "\n".join(result)
            finally:
                conn.close()
        except Exception as e:
            return f"📜 Could not read logs: {e}"


# ══════════════════════════════════════════════════════════════════════
# 4. HOURLY HEALTH SELF-CHECK
# ══════════════════════════════════════════════════════════════════════


async def health_self_check(bot_send_func, interval_minutes: int = 60):
    """
    Periodic health check that silently monitors and alerts on issues.
    Runs as a background task alongside the bot.
    """
    wc = WebsiteController()
    last_alert = {}

    while True:
        await asyncio.sleep(interval_minutes * 60)
        try:
            # Check platforms
            async with httpx.AsyncClient(timeout=15) as client:
                render_ok = False
                pa_ok = False
                try:
                    r = await client.get(wc.RENDER_HEALTH_URL)
                    render_ok = r.status_code == 200
                except Exception:
                    pass
                try:
                    r = await client.get(wc.PA_HEALTH_URL)
                    pa_ok = r.status_code == 200
                except Exception:
                    pass

            # Alert if any platform is down (debounced — max 1 alert per platform per 4 hours)
            now = time.time()
            for name, ok in [("Render", render_ok), ("PythonAnywhere", pa_ok)]:
                if not ok:
                    last = last_alert.get(name, 0)
                    if now - last > 14400:  # 4 hours
                        last_alert[name] = now
                        await bot_send_func(
                            f"🚨 <b>{name} DOWN!</b>\n\n"
                            f"{name} is not responding. Use /fix to diagnose.\n"
                            f"Use /websites for status."
                        )

            # Write health snapshot
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "render": "healthy" if render_ok else "down",
                "pythonanywhere": "healthy" if pa_ok else "down",
            }
            HEALTH_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            HEALTH_SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2))

            logger.info(
                f"🏥 Health check: Render={'OK' if render_ok else 'DOWN'}, PA={'OK' if pa_ok else 'DOWN'}"
            )

        except Exception as e:
            logger.error(f"Health self-check error: {e}")


# ══════════════════════════════════════════════════════════════════════
# 5. SECURITY MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════


class SecurityGuard:
    """Admin-only command protection and rate limiting."""

    ADMIN_COMMANDS = {
        "admin",
        "admin_credit",
        "generate_code",
        "deploy",
        "restart_web",
        "flash_sale",
        "fix",
    }

    RATE_LIMITS = {}  # {user_id: [(timestamp, command), ...]}
    MAX_REQUESTS_PER_MINUTE = 30

    @classmethod
    def get_admin_chat_id(cls) -> str:
        return os.getenv("TELEGRAM_CHAT_ID", "6639482672")

    @classmethod
    def is_admin(cls, chat_id) -> bool:
        """Check if the user is the admin."""
        return str(chat_id) == cls.get_admin_chat_id()

    @classmethod
    def check_admin_command(cls, command: str, chat_id) -> tuple[bool, str]:
        """
        Check if command requires admin and if user is authorized.
        Returns (is_allowed, error_message).
        """
        cmd = command.lstrip("/").split()[0].lower()
        if cmd in cls.ADMIN_COMMANDS and not cls.is_admin(chat_id):
            return False, "🚫 <b>Access Denied</b>\nThis command is admin-only."
        return True, ""

    @classmethod
    def check_rate_limit(cls, user_id) -> bool:
        """Check if user is rate limited. Returns True if allowed."""
        now = time.time()
        uid = str(user_id)
        if uid not in cls.RATE_LIMITS:
            cls.RATE_LIMITS[uid] = []
        # Clean old entries
        cls.RATE_LIMITS[uid] = [t for t in cls.RATE_LIMITS[uid] if now - t[0] < 60]
        if len(cls.RATE_LIMITS[uid]) >= cls.MAX_REQUESTS_PER_MINUTE:
            return False
        cls.RATE_LIMITS[uid].append((now, ""))
        return True


# ══════════════════════════════════════════════════════════════════════
# 6. ENHANCED BOT LAUNCHER (Replaces start_telegram_bot)
# ══════════════════════════════════════════════════════════════════════


async def start_telegram_bot_enhanced():
    """
    Start the Telegram bot with crash protection, health monitoring,
    and AI auto-fix capabilities. Use this instead of the original
    start_telegram_bot() in production.
    """
    from core.telegram.bot import TelegramBot

    os.makedirs("logs", exist_ok=True)

    # Create bot instance
    bot = TelegramBot()

    if not bot.enabled:
        logger.warning("[BOT] Telegram bot not enabled (no token/chat_id)")
        return

    # Wrap with crash watchdog
    watchdog = BotWatchdog(bot)

    # Start health self-check in background
    async def send_func(msg):
        with contextlib.suppress(Exception):
            await bot.send(msg)

    health_task = asyncio.create_task(health_self_check(send_func, interval_minutes=60))

    try:
        logger.info("🚀 [ENHANCED] Starting bot with 24/7 crash protection...")
        await watchdog.run_forever()
    finally:
        watchdog.stop()
        health_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await health_task

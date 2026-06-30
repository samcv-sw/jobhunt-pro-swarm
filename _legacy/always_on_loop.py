import time
import os
import sys
import gc
import logging
import asyncio
import io
from datetime import datetime, timezone

# ── Fix Windows console encoding for emoji-safe logging ──
if sys.stdout.encoding is None or sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding is None or sys.stderr.encoding.upper() not in ("UTF-8", "UTF8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Resolve paths dynamically to support both local and PythonAnywhere environments
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - ALWAYS-ON - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "always_on.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting Always-on Campaign Loop — MAXIMUM THROUGHPUT MODE v2.1")

# Add project root to path
sys.path.insert(0, base_dir)

# ── Telegram Alert Helper ──
async def send_telegram_alert(message: str):
    """Attempt to send a Telegram alert on startup or critical crash."""
    try:
        from core.auto_heal import _telegram_alert
        await _telegram_alert(message)
    except Exception as e:
        logger.debug(f"Failed to send Telegram alert: {e}")

# ── Adaptive sleep intervals ──────────────────────────────────────────────────
_SLEEP_ACTIVE   = 1     # campaigns were processed — run again immediately
_SLEEP_IDLE_1   = 3     # 1-5 empty cycles
_SLEEP_IDLE_2   = 10    # 6-15 empty cycles
_SLEEP_IDLE_3   = 30    # 16+ empty cycles (PA free worker has nothing to do)
_SLEEP_ERROR    = 5     # single error
_SLEEP_ERROR_CB = 60    # circuit-breaker: 5+ consecutive errors

# ── Health logging every N cycles ─────────────────────────────────────────────
_HEALTH_LOG_INTERVAL = 50


async def run_loop():
    consecutive_empty  = 0
    consecutive_errors = 0
    total_cycles       = 0
    total_sent         = 0
    loop_start         = time.monotonic()

    # Send startup alert
    await send_telegram_alert(
        "🚀 <b>Always-On Loop Started</b>\n"
        f"Uptime monitoring initiated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC.\n"
        "<i>Running on maximum throughput mode.</i>"
    )

    try:
        while True:
            total_cycles += 1
            cycle_start   = time.monotonic()

            # ── Periodic health report ────────────────────────────────────────────
            if total_cycles % _HEALTH_LOG_INTERVAL == 0:
                uptime_min = (time.monotonic() - loop_start) / 60
                logger.info(
                    f"[Health] cycle={total_cycles} | total_sent={total_sent} | "
                    f"uptime={uptime_min:.1f}min | empty_streak={consecutive_empty} | "
                    f"error_streak={consecutive_errors}"
                )

            logger.info(f"Triggering campaign run cycle #{total_cycles}...")
            sleep_time = _SLEEP_ACTIVE

            try:
                from core.multi_tenant import MultiTenantRunner
                runner = MultiTenantRunner(company_limit=15, max_campaigns=10)
                result = await runner.tick()

                processed = result.get("campaigns_processed", 0)
                sent      = result.get("emails_sent", 0)
                total_sent += sent

                cycle_ms = int((time.monotonic() - cycle_start) * 1000)
                logger.info(
                    f"Cycle #{total_cycles} done in {cycle_ms}ms: "
                    f"processed={processed} campaigns, sent={sent} applications"
                )

                # Reset error streak on success
                consecutive_errors = 0

                if processed > 0:
                    sleep_time     = _SLEEP_ACTIVE
                    consecutive_empty = 0
                else:
                    consecutive_empty += 1
                    if consecutive_empty <= 5:
                        sleep_time = _SLEEP_IDLE_1
                    elif consecutive_empty <= 15:
                        sleep_time = _SLEEP_IDLE_2
                    else:
                        sleep_time = _SLEEP_IDLE_3

            except Exception as e:
                consecutive_errors += 1
                consecutive_empty  += 1
                logger.error(f"Error in cycle #{total_cycles}: {e}", exc_info=True)

                if consecutive_errors >= 5:
                    logger.critical(
                        f"[Circuit] {consecutive_errors} consecutive errors — "
                        f"backing off {_SLEEP_ERROR_CB}s to prevent crash loop"
                    )
                    await send_telegram_alert(
                        "⚠️ <b>Always-On Loop Warning</b>\n"
                        f"Encountered {consecutive_errors} consecutive loop errors.\n"
                        f"<b>Last Error:</b> <code>{str(e)[:150]}</code>\n"
                        f"<i>Backing off for {_SLEEP_ERROR_CB}s.</i>"
                    )
                    sleep_time = _SLEEP_ERROR_CB
                else:
                    sleep_time = _SLEEP_ERROR

            # ── Periodic GC to reclaim memory on PA free tier (512MB limit) ──────
            if total_cycles % 10 == 0:
                collected = gc.collect()
                logger.debug(f"[GC] collected {collected} objects")

            logger.info(f"Sleeping {sleep_time}s (empty_streak={consecutive_empty}, error_streak={consecutive_errors})...")
            await asyncio.sleep(sleep_time)
            
    except asyncio.CancelledError:
        logger.info("Always-on loop cancelled gracefully.")
    except Exception as fatal_err:
        logger.critical(f"FATAL: Always-on loop crashed: {fatal_err}", exc_info=True)
        await send_telegram_alert(
            "🚨 <b>Always-On Loop CRASHED</b>\n"
            f"<b>Fatal Exception:</b> <code>{str(fatal_err)[:200]}</code>\n"
            "<i>The background worker has stopped running.</i>"
        )
        raise fatal_err


if __name__ == "__main__":
    asyncio.run(run_loop())

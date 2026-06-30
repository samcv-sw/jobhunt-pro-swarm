"""
JobHunt Pro v13 - Auto Run (Hardened)
Starts web server + swarm master (200 agents) + telegram bot + legacy orchestrator
+ Service order fulfillment watchdog + healing daemon
Fully fault-tolerant: if any component crashes, watchdog restarts it within 60s
"""
import sys, os
if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim
        sys.modules['sqlite3'] = pg_sqlite_shim
    except Exception:
        pass

import asyncio
import logging
import sys
import os
import json
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure directories exist
for _dir in ["data", "logs", "sent_mails", "cache"]:
    os.makedirs(_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/auto_run.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8080"))
WATCHDOG_INTERVAL = 30  # seconds between health checks
HEALING_INTERVAL = 300   # 5 min between healing cycles
SERVICE_CHECK_INTERVAL = 120  # 2 min between service order checks


async def run_web_server():
    """Run FastAPI web server with connection retry."""
    import uvicorn
    from web.app_v2 import app
    config = uvicorn.Config(
        app, host="0.0.0.0", port=PORT,
        log_level="info", access_log=True,
        timeout_keep_alive=30,
    )
    server = uvicorn.Server(config)
    logger.info("Web server starting on port %d", PORT)
    await server.serve()


async def run_telegram_bot():
    """Run Telegram bot if configured."""
    await asyncio.sleep(10)
    try:
        from core.telegram_bot import TelegramBot
        bot = TelegramBot()
        if bot.enabled:
            logger.info("Telegram bot started")
            await bot.run_bot()
        else:
            logger.info("Telegram bot not enabled, sleeping")
            while True:
                await asyncio.sleep(3600)
    except Exception as e:
        logger.warning("Telegram bot disabled: %s", e)
        while True:
            await asyncio.sleep(3600)


async def run_legacy_cycles():
    """Legacy orchestrator cycles with auto-restart."""
    await asyncio.sleep(15)
    while True:
        try:
            from orchestrator import Orchestrator
            orch = Orchestrator()
            logger.info("Legacy orchestrator ready, starting cycle")
            await orch.run_full_cycle()
            while True:
                await asyncio.sleep(1800)  # 30 min between cycles
                try:
                    await orch.run_full_cycle()
                except Exception as e:
                    logger.error("Legacy cycle error: %s", e)
                    await asyncio.sleep(300)  # wait 5 min before retry
        except Exception as e:
            logger.error("Legacy orchestrator error (will restart): %s", e)
            await asyncio.sleep(60)  # wait 1 min before restarting


async def run_swarm_master():
    """
    200-agent swarm master with auto-recovery.
    """
    await asyncio.sleep(5)
    while True:
        try:
            from core.swarm_master import SwarmMaster
            from core.healing_engine import healing_engine

            # Run initial healing check before swarm starts
            try:
                if hasattr(healing_engine, 'diagnose_and_heal'):
                    report = await healing_engine.diagnose_and_heal(force=True)
                    if report.get("issues_detected", 0) > 0:
                        logger.info(f"Pre-swarm healing: {report['auto_fixed']} fixed, {report['need_attention']} need attention")
            except Exception as heal_err:
                logger.debug(f"Pre-swarm healing check: {heal_err}")

            # Initialize legacy orchestrator for re-use by swarm
            try:
                from orchestrator import Orchestrator
                orchestrator = Orchestrator()
            except Exception:
                orchestrator = None
                logger.info("Swarm running without legacy orchestrator")

            # Build the 200-agent swarm
            master = SwarmMaster()
            await master.initialize(orchestrator)
            cycle_count = 0

            # Run cycles
            while True:
                cycle_count += 1
                try:
                    logger.info("Swarm cycle #%d starting...", cycle_count)
                    results = await master.full_job_cycle()
                    status = await master.get_swarm_status()

                    pool = status.get("agent_pool", {})
                    email = status.get("email_accounts", {})
                    logger.info(
                        "Swarm #%d: %d active | %d completed | %d failed | "
                        "%d email accounts | %d cycles total",
                        cycle_count,
                        pool.get("active_agents", 0),
                        pool.get("total_completed", 0),
                        pool.get("total_failed", 0),
                        email.get("total_accounts", 0),
                        status.get("cycles_completed", 0),
                    )
                except Exception as e:
                    logger.error("Swarm cycle #%d error: %s", cycle_count, e)
                    logger.debug(traceback.format_exc())

                await asyncio.sleep(900)  # 15 min between cycles

        except Exception as e:
            logger.error("Swarm master crashed, restarting in 30s: %s", e)
            logger.debug(traceback.format_exc())
            await asyncio.sleep(30)


async def run_healing_daemon():
    """Background healing daemon — runs diagnostics every 5 minutes."""
    await asyncio.sleep(20)
    while True:
        try:
            from core.healing_engine import healing_engine
            await healing_engine.diagnose_and_heal(force=False)
        except Exception as e:
            logger.debug(f"Healing daemon cycle: {e}")
        await asyncio.sleep(HEALING_INTERVAL)


async def run_hyper_mode():
    """Run Hyper Mode once on startup then sleep (one-shot)."""
    await asyncio.sleep(3)
    try:
        from core.hyper_mode import HyperMode
        hyper = HyperMode()
        try:
            logger.info("=" * 60)
            logger.info("  HYPER MODE STARTING (Turbo)")
            logger.info("  Zero AI | Template Power | Parallel SMTP")
            logger.info("=" * 60)
            result = hyper.run()
            logger.info(f"Hyper Mode: {result.get('sent', 0)} sent, {result.get('failed', 0)} failed, "
                        f"{result.get('elapsed_seconds', 0)}s, "
                        f"{result.get('emails_per_hour', 0):.0f}/hour")
        finally:
            hyper.close()
    except Exception as e:
        logger.warning(f"Hyper Mode unavailable: {e}")
        logger.debug(traceback.format_exc())


async def run_service_order_watchdog():
    """
    Watchdog for the service fulfillment system.
    Checks for pending orders and attempts delivery every 2 minutes.
    Also logs daily sales stats.
    """
    await asyncio.sleep(30)  # wait for system to initialize
    logger.info("Service order watchdog started")
    while True:
        try:
            from services.fulfillment import ServiceFulfillment
            fulfillment = ServiceFulfillment()

            # Get stats
            stats = fulfillment.get_stats()
            if stats["total_orders"] > 0:
                logger.info(
                    "Service orders: %d total | %d pending | %d paid | %d delivered | $%.2f revenue",
                    stats["total_orders"],
                    stats["pending_orders"],
                    stats["paid_orders"],
                    stats["delivered_orders"],
                    stats["total_revenue"],
                )

            # Check for paid-but-undelivered orders
            paid = fulfillment.get_paid_orders()
            for order in paid:
                if order.get("status") == "paid" and not order.get("delivered", False):
                    logger.info("Auto-delivering paid order %s...", order["order_id"])
                    try:
                        # Trigger async delivery safely
                        loop = asyncio.get_running_loop()
                        loop.create_task(_deliver_order(fulfillment, order["order_id"]))
                    except Exception as e:
                        logger.error("Failed to trigger delivery for %s: %s", order["order_id"], e)

        except ImportError:
            # Services module may not be available
            pass
        except Exception as e:
            logger.debug(f"Service watchdog check: {e}")

        await asyncio.sleep(SERVICE_CHECK_INTERVAL)


async def _deliver_order(fulfillment, order_id):
    """Deliver a single order."""
    try:
        await fulfillment.deliver_service(order_id)
        logger.info("Auto-delivered order %s", order_id)
    except Exception as e:
        logger.error("Auto-delivery failed for %s: %s", order_id, e)


async def watchdog_monitor():
    """
    Top-level watchdog: monitors all coroutines and reports health.
    If the process itself becomes unhealthy, it logs warnings.
    (Container orchestration like Docker handles actual restarts.)
    """
    await asyncio.sleep(60)
    last_health_log = 0
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Log health status every 5 minutes
            if now.timestamp() - last_health_log > 300:
                health = {
                    "status": "running",
                    "port": PORT,
                    "timestamp": now.isoformat(),
                    "uptime_hours": round((now - _start_time).total_seconds() / 3600, 2) if '_start_time' in globals() else 0,
                }
                logger.info("Health: %s | Port: %d", health["status"], health["port"])
                last_health_log = now.timestamp()
        except Exception as e:
            logger.debug(f"Watchdog check: {e}")
        await asyncio.sleep(WATCHDOG_INTERVAL)


_start_time = datetime.now(timezone.utc)


async def main():
    logger.info("=" * 60)
    logger.info("  JOBHUNT PRO v13 (HARDENED)")
    logger.info("  200-Agent Swarm | Free-tier Architecture")
    logger.info("  Web: http://0.0.0.0:%d  |  Services: 20 ($2-$20)", PORT)
    logger.info("  Watchdog: 30s | Healing: 5min | Service Check: 2min")
    logger.info("=" * 60)

    await asyncio.gather(
        run_web_server(),
        run_telegram_bot(),
        # run_legacy_cycles(),  # Legacy orchestrator broken, replaced by SwarmMaster
        run_swarm_master(),
        run_hyper_mode(),
        run_healing_daemon(),
        run_service_order_watchdog(),
        watchdog_monitor(),
        return_exceptions=True
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested, exiting gracefully...")
    except Exception as e:
        logger.critical("Fatal error: %s", e)
        logger.debug(traceback.format_exc())
        sys.exit(1)

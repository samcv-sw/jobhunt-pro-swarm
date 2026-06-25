"""
JobHunt Pro v16.7 — Mega Swarm Runner (20,000 agents)
=====================================================
Launches the 20,000 hierarchical agent swarm with:
- 18,000 Worker Agents
-  1,500 Squad Leaders (sub-of-sub)
-    500 Team Managers (sub-agent)

Usage:
    python run_mega_swarm.py              # Run a single cycle
    python run_mega_swarm.py --loop       # Run cycles in a loop (30 min interval)
    python run_mega_swarm.py --status     # Show swarm status
"""
import asyncio
import logging
import sys
import os
import time

# Ensure UTF-8 on Windows (for emoji-free output)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auto_install import ensure_packages
ensure_packages()

import config

logging.basicConfig(
    level=getattr(logging, getattr(config, "LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_mega_swarm")


async def run_single_cycle(mega_master) -> int:
    """Run one full mega swarm cycle. Returns total tasks dispatched."""
    logger.info("=" * 70)
    logger.info("  MEGA SWARM CYCLE STARTING — 20,000 agents activating")
    logger.info("=" * 70)

    start = time.time()
    results = await mega_master.full_job_cycle()
    elapsed = time.time() - start

    total_tasks = sum(results.values()) if results else 0
    logger.info("=" * 70)
    logger.info("  MEGA CYCLE COMPLETE in %.1f seconds", elapsed)
    logger.info("  Total tasks dispatched: %d across 20,000 agents", total_tasks)

    if results:
        for phase, count in results.items():
            logger.info("    %-15s: %d tasks", phase, count)

    # Show pool stats
    if mega_master.mega_pool:
        stats = mega_master.mega_pool.get_pool_stats()
        logger.info("  Pool: %d workers, %d squad leaders, %d team managers",
                     stats["total_workers"], stats["total_squad_leaders"],
                     stats["total_team_managers"])

    logger.info("=" * 70)
    return total_tasks


async def run_loop(mega_master, interval_minutes: int = 30):
    """Run mega swarm cycles in a continuous loop."""
    logger.info("Mega Swarm loop mode — interval: %d minutes", interval_minutes)
    cycle = 0
    while True:
        cycle += 1
        logger.info("--- Mega Cycle #%d ---", cycle)
        try:
            await run_single_cycle(mega_master)
        except Exception as e:
            logger.error("Mega cycle #%d failed: %s", cycle, e)

        logger.info("Sleeping %d minutes until next cycle...", interval_minutes)
        await asyncio.sleep(interval_minutes * 60)


async def show_status(mega_master):
    """Display current mega swarm status."""
    status = await mega_master.get_swarm_status()
    print()
    print("=" * 60)
    print("  MEGA SWARM STATUS")
    print("=" * 60)
    print(f"  Status:           {status.get('status', 'N/A')}")
    print(f"  Paused:           {status.get('paused', False)}")
    print(f"  Uptime:           {status.get('uptime_seconds', 0):.1f}s")
    print(f"  Cycles:           {status.get('cycles_completed', 0)}")
    print(f"  Total Agents:     {status.get('total_agents', 0):,}")
    print()
    print("  Worker Breakdown:")
    for atype, count in status.get("worker_breakdown", {}).items():
        print(f"    {atype.value if hasattr(atype, 'value') else atype:20s}: {count:,}")
    print()
    print(f"  Squad Leaders:    {status.get('total_squad_leaders', 0):,}")
    print(f"  Team Managers:    {status.get('total_team_managers', 0):,}")
    print()

    pool = status.get("pool", {})
    if pool:
        print("  Pool Summary:")
        print(f"    Workers:        {pool.get('total_workers', 0):,}")
        print(f"    Squad Leaders:  {pool.get('total_squad_leaders', 0):,}")
        print(f"    Team Managers:  {pool.get('total_team_managers', 0):,}")
        print(f"    Total:          {pool.get('total_agents', 0):,}")
    print("=" * 60)


async def main():
    """Main entry point."""
    from core.mega_swarm import MegaSwarmMaster

    args = set(sys.argv[1:])

    logger.info("Initializing Mega Swarm (20,000 agents)...")
    mega_master = MegaSwarmMaster()
    await mega_master.initialize()

    logger.info("Mega Swarm initialized with 20,000 agents!")

    if "--status" in args:
        await show_status(mega_master)
    elif "--loop" in args:
        await run_loop(mega_master, interval_minutes=30)
    else:
        await run_single_cycle(mega_master)

    # If not in loop mode, shut down
    if "--loop" not in args:
        await mega_master.shutdown()
        logger.info("Mega Swarm shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Mega Swarm interrupted by user.")
    except Exception as e:
        logger.error("Mega Swarm fatal error: %s", e)
        raise

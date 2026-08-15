#!/usr/bin/env python3
"""
scripts/dlq_self_heal.py - 24/7 Automated Dead-Letter Queue Self-Healing Sentinel
Scans failed / dead-letter queues across SQLite, PostgreSQL, and outbox logs,
automatically remediates transient faults, resets retry counters, and reports telemetry.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.dlq_healing import dlq_healer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dlq_cli")

def main():
    parser = argparse.ArgumentParser(description="24/7 DLQ Self-Healing Sentinel")
    parser.add_argument("--status", action="store_true", help="Display current DLQ metrics and exit")
    parser.add_argument("--heal", action="store_true", help="Run self-healing cycle on dead-letter queues")
    parser.add_argument("--force", action="store_true", help="Force heal all failed tasks regardless of error pattern")
    parser.add_argument("--purge-days", type=int, default=0, help="Purge unrecoverable poison pills older than N days")
    args = parser.parse_args()

    if args.purge_days > 0:
        purged = dlq_healer.purge_quarantined_tasks(keep_days=args.purge_days)
        logger.info(f"Purged {purged} ancient dead-letter tasks older than {args.purge_days} days.")

    if args.heal or (not args.status and args.purge_days == 0):
        logger.info("Starting DLQ Self-Healing cycle...")
        result = dlq_healer.heal_dead_letter_queue(max_jobs=100, force_all=args.force)
        logger.info(f"DLQ Healing complete: {result['healed_count']} tasks auto-healed, {result['quarantined_count']} quarantined.")
        if result.get("healed_tasks"):
            for h in result["healed_tasks"]:
                logger.info(f"  -> Healed Task #{h['task_id']} ({h['task_type']})")

    status = dlq_healer.get_dlq_status()
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()

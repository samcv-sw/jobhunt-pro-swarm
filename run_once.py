import asyncio
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

# Fallback SECRET_KEY to prevent web.shared from raising RuntimeError
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "jobhunt-pro-cli-ephemeral-secret-key"

from core.job_queue import dequeue_task, enqueue_task
from core.queue_worker import _process_cron_tick_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run-once")

async def main():
    logger.info("Starting single cycle worker tick...")
    # Enqueue a cron tick task to process pending campaigns and sync engine
    enqueue_task("cron_tick", {})
    # Process the queue here once
    task = dequeue_task()
    if task and task["task_type"] == "cron_tick":
        logger.info(f"Processing dequeued cron_tick task {task['id']}...")
        await _process_cron_tick_task(task["id"])
        logger.info("Cycle worker tick complete.")
    else:
        logger.info("No cron_tick task dequeued or queue empty.")

if __name__ == "__main__":
    asyncio.run(main())

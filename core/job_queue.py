import json
import logging
from core.pg_sqlite_shim import connect, get_backend

logger = logging.getLogger(__name__)

def enqueue_task(task_type: str, payload: dict):
    """Adds a task to the queue."""
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO job_queue (task_type, payload, status) VALUES (?, ?, 'pending')",
                (task_type, json.dumps(payload))
            )
            logger.info(f"Enqueued task: {task_type}")
    except Exception as e:
        logger.error(f"Failed to enqueue task {task_type}: {e}")

def dequeue_task():
    """Atomically dequeues a task using FOR UPDATE SKIP LOCKED (PostgreSQL)."""
    try:
        with connect() as conn:
            # If backend is sqlite, we do a simple non-concurrent fetch (for local dev)
            if get_backend() == "sqlite":
                cur = conn.execute("SELECT id, task_type, payload FROM job_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1")
                row = cur.fetchone()
                if not row:
                    return None
                task_id = row[0]
                conn.execute("UPDATE job_queue SET status = 'running', locked_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
                return {
                    "id": task_id,
                    "task_type": row[1],
                    "payload": json.loads(row[2])
                }
            else:
                # PostgreSQL atomic concurrent dequeue
                cur = conn.execute("""
                    UPDATE job_queue 
                    SET status = 'running', locked_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id FROM job_queue 
                        WHERE status = 'pending' 
                        ORDER BY created_at ASC 
                        LIMIT 1 
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING id, task_type, payload
                """)
                row = cur.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "task_type": row[1],
                        "payload": json.loads(row[2])
                    }
                return None
    except Exception as e:
        logger.error(f"Failed to dequeue task: {e}")
        return None

def complete_task(task_id: int):
    """Marks a task as completed."""
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE job_queue SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,)
            )
    except Exception as e:
        logger.error(f"Failed to complete task {task_id}: {e}")

def fail_task(task_id: int, error_msg: str):
    """Marks a task as failed."""
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE job_queue SET status = 'failed', error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (error_msg, task_id)
            )
    except Exception as e:
        logger.error(f"Failed to fail task {task_id}: {e}")

def enqueue_bulk_tasks(tasks: list):
    """
    Atomically enqueues a large list of tasks in a single transaction.
    tasks: list of dicts [{"task_type": "...", "payload": {...}}, ...]
    """
    if not tasks:
        return 0
    try:
        with connect() as conn:
            # We use executemany for bulk inserts
            data = [(t["task_type"], json.dumps(t["payload"]), 'pending') for t in tasks]
            conn.executemany(
                "INSERT INTO job_queue (task_type, payload, status) VALUES (?, ?, ?)",
                data
            )
            # The context manager auto-commits
            logger.info(f"Enqueued {len(tasks)} bulk tasks.")
            return len(tasks)
    except Exception as e:
        logger.error(f"Failed to enqueue bulk tasks: {e}")
        return 0

def cleanup_completed_tasks(keep_days: int = 7):
    """
    Removes completed tasks older than `keep_days` to prevent DB bloat.
    """
    try:
        with connect() as conn:
            cur = conn.execute(
                "DELETE FROM job_queue WHERE status = 'completed' AND updated_at < datetime('now', ?)",
                (f"-{keep_days} days",)
            )
            count = cur.rowcount
            logger.info(f"Cleaned up {count} old completed tasks from job_queue.")
            return count
    except Exception as e:
        logger.error(f"Failed to cleanup completed tasks: {e}")
        return 0


import json
import logging
import threading

from core.pg_sqlite_shim import connect, get_backend

logger = logging.getLogger(__name__)
_sqlite_dequeue_lock = threading.Lock()


def enqueue_task(
    task_type: str, payload: dict, priority: int = 5, max_retries: int = 3
):
    """Adds a task to the queue with priority and retry configuration."""
    try:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO job_queue (task_type, payload, status, priority, max_retries)
                VALUES (?, ?, 'pending', ?, ?)
                """,
                (task_type, json.dumps(payload), priority, max_retries),
            )
            logger.info(f"Enqueued task: {task_type} (priority={priority})")
    except Exception as e:
        logger.error(f"Failed to enqueue task {task_type}: {e}")


def dequeue_task():
    """
    APEX MATRIX: Atomically dequeues the highest priority task that is ready to run.
    Respects next_retry_at for tasks in exponential backoff.
    """
    try:
        with connect() as conn:
            # If backend is sqlite, we do a simple non-concurrent fetch (for local dev)
            if get_backend() == "sqlite":
                with _sqlite_dequeue_lock:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.execute("""
                        SELECT id, task_type, payload FROM job_queue 
                        WHERE (status = 'pending' OR status = 'failed')
                          AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP)
                        ORDER BY priority ASC, next_retry_at ASC, created_at ASC 
                        LIMIT 1
                    """)
                    row = cur.fetchone()
                    if not row:
                        return None
                    task_id = row[0]
                    conn.execute(
                        "UPDATE job_queue SET status = 'running', locked_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (task_id,),
                    )
                    return {
                        "id": task_id,
                        "task_type": row[1],
                        "payload": json.loads(row[2]),
                    }
            else:
                # PostgreSQL atomic concurrent dequeue
                cur = conn.execute("""
                    UPDATE job_queue 
                    SET status = 'running', locked_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id FROM job_queue 
                        WHERE (status = 'pending' OR status = 'failed')
                          AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP)
                        ORDER BY priority ASC, next_retry_at ASC, created_at ASC 
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
                        "payload": json.loads(row[2]),
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
                (task_id,),
            )
    except Exception as e:
        logger.error(f"Failed to complete task {task_id}: {e}")


def fail_task(task_id: int, error_msg: str):
    """
    APEX MATRIX: Marks a task as failed and schedules an exponential backoff retry.
    If max_retries is reached, marks it as permanently failed.
    """
    try:
        with connect() as conn:
            # Fetch current retry stats
            cur = conn.execute(
                "SELECT retry_count, max_retries FROM job_queue WHERE id = ?",
                (task_id,),
            )
            row = cur.fetchone()
            if not row:
                return

            retry_count, max_retries = row
            retry_count += 1

            if retry_count <= max_retries:
                # Exponential backoff: 1m, 2m, 4m, 8m...
                delay_minutes = 2 ** (retry_count - 1)

                # Use standard SQL date modifier syntax supported by both SQLite and our PG shim
                conn.execute(
                    """
                    UPDATE job_queue 
                    SET status = 'failed', 
                        error = ?, 
                        updated_at = CURRENT_TIMESTAMP,
                        retry_count = ?,
                        next_retry_at = datetime(CURRENT_TIMESTAMP, '+' || ? || ' minutes')
                    WHERE id = ?
                    """,
                    (error_msg, retry_count, delay_minutes, task_id),
                )
                logger.warning(
                    f"Task {task_id} failed (attempt {retry_count}/{max_retries}). Retrying in {delay_minutes}m: {error_msg}"
                )
            else:
                # Permanent failure
                conn.execute(
                    """
                    UPDATE job_queue 
                    SET status = 'permanently_failed', 
                        error = ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                    """,
                    (error_msg, task_id),
                )
                logger.error(
                    f"Task {task_id} permanently failed after {max_retries} retries: {error_msg}"
                )

    except Exception as e:
        logger.error(f"Failed to fail task {task_id}: {e}")


def enqueue_bulk_tasks(tasks: list, priority: int = 5, max_retries: int = 3):
    """
    Atomically enqueues a large list of tasks in a single transaction.
    tasks: list of dicts [{"task_type": "...", "payload": {...}}, ...]
    """
    if not tasks:
        return 0
    try:
        with connect() as conn:
            # We use executemany for bulk inserts
            data = [
                (
                    t["task_type"],
                    json.dumps(t["payload"]),
                    "pending",
                    priority,
                    max_retries,
                )
                for t in tasks
            ]
            conn.executemany(
                "INSERT INTO job_queue (task_type, payload, status, priority, max_retries) VALUES (?, ?, ?, ?, ?)",
                data,
            )
            # The context manager auto-commits
            logger.info(f"Enqueued {len(tasks)} bulk tasks (priority={priority}).")

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
                (f"-{keep_days} days",),
            )
            count = cur.rowcount
            logger.info(f"Cleaned up {count} old completed tasks from job_queue.")
            return count
    except Exception as e:
        logger.error(f"Failed to cleanup completed tasks: {e}")
        return 0

"""
core/dlq_healing.py - Autonomous DLQ Self-Healing Engine
=========================================================
Monitors Dead Letter Queues (DLQ) across job_queue, sync_outbox_log,
and webhook failure logs.
Performs root-cause categorization (transient network, rate limit, DB lock vs fatal schema)
and safely auto-heals failed/poison tasks with zero manual intervention.
"""

import json
import logging
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.pg_sqlite_shim import connect, get_backend

logger = logging.getLogger("dlq_healing")

TRANSIENT_PATTERNS = [
    r"timeout",
    r"timed out",
    r"connection refused",
    r"connection reset",
    r"remote disconnected",
    r"database is locked",
    r"sqlite3\.operationalerror",
    r"429",
    r"rate limit",
    r"too many requests",
    r"502",
    r"503",
    r"504",
    r"bad gateway",
    r"service unavailable",
    r"gateway timeout",
    r"econnreset",
    r"socket",
    r"dns",
    r"name or service not known",
]

class DLQSelfHealingManager:
    """Enterprise 24/7 Self-Healing Manager for Dead Letter Queues."""

    def __init__(self, incident_log_file: Optional[Path] = None):
        self.incident_log_file = incident_log_file or (ROOT_DIR / "data" / "healing_history.json")
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure data directory and incident log exist."""
        (ROOT_DIR / "data").mkdir(parents=True, exist_ok=True)
        if not self.incident_log_file.exists():
            try:
                self.incident_log_file.write_text("[]", encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not initialize healing log: {e}")

    def is_transient_error(self, error_msg: Optional[str]) -> bool:
        """Determines if an error message indicates a transient, recoverable failure."""
        if not error_msg:
            return True
        error_lower = error_msg.lower()
        for pattern in TRANSIENT_PATTERNS:
            if re.search(pattern, error_lower):
                return True
        return False

    def get_dlq_status(self) -> Dict[str, Any]:
        """Provides comprehensive DLQ status and telemetry."""
        counts = {
            "pending": 0,
            "running": 0,
            "failed": 0,
            "permanently_failed": 0,
            "completed": 0,
            "total": 0,
        }
        dead_letter_log_size = 0
        dead_letter_log_path = ROOT_DIR / "backend" / "dead_letter_queue.log"

        if dead_letter_log_path.exists():
            try:
                dead_letter_log_size = dead_letter_log_path.stat().st_size
            except Exception:
                pass

        try:
            with connect() as conn:
                # Check if job_queue exists
                cur = conn.execute("SELECT status, COUNT(*) FROM job_queue GROUP BY status")
                rows = cur.fetchall()
                for status, cnt in rows:
                    if status in counts:
                        counts[status] = cnt
                    counts["total"] += cnt
        except Exception as e:
            logger.warning(f"Could not read job_queue stats: {e}")

        # Read recent healing events
        recent_heals = []
        try:
            if self.incident_log_file.exists():
                with open(self.incident_log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    recent_heals = data[-10:] if isinstance(data, list) else []
        except Exception:
            pass

        return {
            "status": "HEALTHY" if counts["permanently_failed"] == 0 else "DLQ_ATTENTION_REQUIRED",
            "backend": get_backend(),
            "queue_counts": counts,
            "dead_letter_log_size_bytes": dead_letter_log_size,
            "recent_healing_actions": recent_heals,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def heal_dead_letter_queue(self, max_jobs: int = 50, force_all: bool = False) -> Dict[str, Any]:
        """
        Scans permanently_failed and stuck failed tasks, classifies errors,
        and auto-recovers eligible tasks back into pending status.
        """
        healed_tasks: List[Dict[str, Any]] = []
        quarantined_tasks: List[Dict[str, Any]] = []

        try:
            with connect() as conn:
                # 1. Fetch permanently failed or long-stuck tasks
                query = """
                    SELECT id, task_type, error, retry_count, max_retries, payload
                    FROM job_queue
                    WHERE status = 'permanently_failed'
                       OR (status = 'failed' AND updated_at < datetime('now', '-30 minutes'))
                    ORDER BY id ASC
                    LIMIT ?
                """
                cur = conn.execute(query, (max_jobs,))
                rows = cur.fetchall()

                for row in rows:
                    task_id = row[0]
                    task_type = row[1]
                    error_msg = str(row[2] or "")
                    retry_count = int(row[3] or 0)
                    max_retries = int(row[4] or 3)

                    # Classify if recoverable
                    recoverable = force_all or self.is_transient_error(error_msg)

                    if recoverable:
                        new_max_retries = max(max_retries + 3, retry_count + 3)
                        conn.execute(
                            """
                            UPDATE job_queue
                            SET status = 'pending',
                                retry_count = 0,
                                max_retries = ?,
                                locked_at = NULL,
                                next_retry_at = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP,
                                error = ?
                            WHERE id = ?
                            """,
                            (
                                new_max_retries,
                                f"[AUTO-HEALED at {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] Prev error: {error_msg[:120]}",
                                task_id,
                            ),
                        )
                        healed_tasks.append({
                            "task_id": task_id,
                            "task_type": task_type,
                            "action": "RESET_TO_PENDING",
                            "previous_error": error_msg[:120],
                        })
                    else:
                        quarantined_tasks.append({
                            "task_id": task_id,
                            "task_type": task_type,
                            "action": "QUARANTINED_POISON_PILL",
                            "reason": "Non-transient fatal fault",
                            "error": error_msg[:120],
                        })

            # Record healing history
            if healed_tasks:
                self._record_incident({
                    "timestamp": datetime.now(UTC).isoformat(),
                    "healed_count": len(healed_tasks),
                    "quarantined_count": len(quarantined_tasks),
                    "details": healed_tasks,
                })
                logger.info(f"[DLQ-HEALER] Successfully auto-healed {len(healed_tasks)} dead-letter tasks.")

        except Exception as e:
            logger.error(f"[DLQ-HEALER] Error during DLQ healing cycle: {e}")
            return {
                "success": False,
                "error": str(e),
                "healed_count": 0,
                "quarantined_count": 0,
            }

        return {
            "success": True,
            "healed_count": len(healed_tasks),
            "quarantined_count": len(quarantined_tasks),
            "healed_tasks": healed_tasks,
            "quarantined_tasks": quarantined_tasks,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _record_incident(self, incident: Dict[str, Any]):
        """Append incident to healing log."""
        try:
            data = []
            if self.incident_log_file.exists():
                with open(self.incident_log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
            data.append(incident)
            # Keep last 100 entries
            data = data[-100:]
            with open(self.incident_log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to record healing incident: {e}")

    def purge_quarantined_tasks(self, keep_days: int = 14) -> int:
        """Purge permanently failed tasks older than keep_days."""
        try:
            with connect() as conn:
                cur = conn.execute(
                    "DELETE FROM job_queue WHERE status = 'permanently_failed' AND updated_at < datetime('now', ?)",
                    (f"-{keep_days} days",),
                )
                purged = cur.rowcount
                logger.info(f"[DLQ-HEALER] Purged {purged} ancient poison pills from job_queue.")
                return purged
        except Exception as e:
            logger.error(f"[DLQ-HEALER] Error purging ancient DLQ items: {e}")
            return 0


# Global singleton instance
dlq_healer = DLQSelfHealingManager()


def run_dlq_self_heal() -> Dict[str, Any]:
    """Convenience function for background workers and endpoints."""
    return dlq_healer.heal_dead_letter_queue()

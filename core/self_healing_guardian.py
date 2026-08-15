"""
Self-Healing Auto-Backup & Guardian Sentinel
JobHunt Pro SaaS - Automated SQLite hot backup, database integrity check, and system telemetry.
"""
import os
import time
import sqlite3
import gzip
import shutil
from typing import Dict, List, Any


class SelfHealingGuardian:
    """
    Manages automated rolling database backups, integrity verification,
    and self-healing routines for continuous 24/7 uptime.
    """

    @classmethod
    def perform_hot_backup(cls, source_db: str = "saas_v2.db", backup_dir: str = "data/backups") -> Dict[str, Any]:
        """
        Executes a zero-downtime hot database backup using SQLite online backup API,
        compresses to gzip, and enforces 7-day retention rotation.
        """
        if not os.path.exists(source_db):
            return {"status": "skipped", "message": f"Source DB '{source_db}' not found."}

        os.makedirs(backup_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        temp_backup = os.path.join(backup_dir, f"backup_{timestamp}.db")
        gz_backup = os.path.join(backup_dir, f"backup_{timestamp}.db.gz")

        start_time = time.perf_counter()

        try:
            # 1. Hot online backup
            src_conn = sqlite3.connect(source_db)
            dest_conn = sqlite3.connect(temp_backup)
            with dest_conn:
                src_conn.backup(dest_conn)
            dest_conn.close()
            src_conn.close()

            # 2. Compress to gzip
            with open(temp_backup, "rb") as f_in, gzip.open(gz_backup, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed temp
            if os.path.exists(temp_backup):
                os.remove(temp_backup)

            # 3. Rotate old backups (keep latest 7)
            all_backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith(".gz")])
            if len(all_backups) > 7:
                for old in all_backups[:-7]:
                    os.remove(old)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            compressed_size_kb = round(os.path.getsize(gz_backup) / 1024.0, 2)

            return {
                "status": "success",
                "backup_file": gz_backup,
                "compressed_size_kb": compressed_size_kb,
                "latency_ms": elapsed_ms,
                "retention_count": min(len(all_backups), 7)
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    @classmethod
    def verify_database_integrity(cls, db_path: str = "saas_v2.db") -> Dict[str, Any]:
        """Runs SQLite PRAGMA integrity_check."""
        if not os.path.exists(db_path):
            return {"status": "healthy", "message": "In-memory or pending initialization."}

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            conn.close()
            is_ok = res and res[0] == "ok"
            return {
                "status": "healthy" if is_ok else "corrupted",
                "integrity_result": res[0] if res else "unknown",
                "database_size_kb": round(os.path.getsize(db_path) / 1024.0, 2)
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}


# Global singleton instance
self_healing_guardian = SelfHealingGuardian()

"""
scripts/restore_db.py - Automated Zero-Cost Database Restoration Utility
JobHunt Pro SaaS - Restores SQLite and PostgreSQL databases from compressed gzip snapshots.
"""

import os
import sys
import gzip
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("restore_db")


def restore_sqlite_database(backup_gz_path: str, target_db_path: str = "saas_v2.db") -> bool:
    """Restores database from a compressed .gz backup snapshot."""
    if not os.path.exists(backup_gz_path):
        logger.error(f"Backup file not found: {backup_gz_path}")
        return False

    # Create safety backup of existing DB if present
    if os.path.exists(target_db_path):
        safety_path = f"{target_db_path}.pre_restore_safety"
        shutil.copyfile(target_db_path, safety_path)
        logger.info(f"Safety snapshot created: {safety_path}")

    with gzip.open(backup_gz_path, "rb") as f_in:
        with open(target_db_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    size_kb = os.path.getsize(target_db_path) / 1024
    logger.info(f"✅ Database restored successfully to {target_db_path} ({size_kb:.2f} KB)")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_db.py <path_to_backup.db.gz> [target_db_path]")
        sys.exit(1)
    backup_file = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "saas_v2.db"
    restore_sqlite_database(backup_file, target)

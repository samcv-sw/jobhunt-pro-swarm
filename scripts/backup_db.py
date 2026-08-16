#!/usr/bin/env python3
"""
scripts/backup_db.py - Automated Zero-Cost Database Backup Utility
JobHunt Pro SaaS - Creates compressed gzip snapshots of SQLite and PostgreSQL databases.
"""

import os
import sys
import gzip
import shutil
import datetime
import logging

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backup_db")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_DIR = os.path.join(ROOT_DIR, "data", "backups")


def backup_sqlite_database(db_path: str = None, destination_dir: str = BACKUP_DIR) -> str:
    """Creates a compressed .gz backup snapshot of an active SQLite database."""
    os.makedirs(destination_dir, exist_ok=True)
    
    if not db_path:
        candidates = [
            os.path.join(ROOT_DIR, "data", "jobhunt_saas_v2.db"),
            os.path.join(ROOT_DIR, "jobhunt_saas_v2.db"),
            os.path.join(ROOT_DIR, "saas_v2.db"),
            os.path.join(ROOT_DIR, "jobhunt.db"),
        ]
        for c in candidates:
            if os.path.exists(c):
                db_path = c
                break

    if not db_path or not os.path.exists(db_path):
        logger.warning(f"[!] Database path '{db_path}' not found. Aborting backup.")
        return ""

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(db_path))[0]
    out_file = os.path.join(destination_dir, f"{base_name}_{timestamp}.db.gz")

    with open(db_path, "rb") as f_in:
        with gzip.open(out_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    size_kb = os.path.getsize(out_file) / 1024
    print("====================================================================")
    print(f" [OK] Database backup created successfully:")
    print(f" [*] Source Database : {os.path.relpath(db_path, ROOT_DIR)}")
    print(f" [*] Snapshot Archive: {os.path.abspath(out_file)} ({size_kb:.2f} KB)")
    print("====================================================================")
    return out_file


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    backup_sqlite_database(target)

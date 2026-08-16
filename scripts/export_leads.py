#!/usr/bin/env python3
"""
JobHunt Pro - Leads and Prospects Exporter
Exports captured ATS magnet leads and scraped prospective employers to CSV / Excel format.
"""
import os
import sys
import csv
import sqlite3
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def export_leads():
    db_candidates = [
        os.path.join(ROOT_DIR, "data", "jobhunt_saas_v2.db"),
        os.path.join(ROOT_DIR, "jobhunt_saas_v2.db"),
        os.path.join(ROOT_DIR, "saas_v2.db"),
        os.path.join(ROOT_DIR, "jobhunt.db"),
    ]
    
    db_path = None
    for candidate in db_candidates:
        if os.path.exists(candidate):
            db_path = candidate
            break
            
    if not db_path:
        print("[!] No active database found in workspace (checked data/jobhunt_saas_v2.db, jobhunt_saas_v2.db).")
        return

    data_out_dir = os.path.join(ROOT_DIR, "data")
    os.makedirs(data_out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = os.path.join(data_out_dir, f"leads_export_{timestamp}.csv")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    target_table = None
    for tbl in ["leads", "harvested_leads", "campaign_sent", "users"]:
        if tbl in tables:
            target_table = tbl
            break

    if not target_table:
        print(f"[!] No leads or contacts table found in database: {db_path}")
        conn.close()
        return

    cur.execute(f"SELECT * FROM {target_table}")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)

    conn.close()

    print("====================================================================")
    print(f" [OK] Successfully exported {len(rows)} record(s) from [{target_table}]")
    print(f" [*] Source Database : {os.path.relpath(db_path, ROOT_DIR)}")
    print(f" [*] Output File     : {os.path.abspath(out_csv)}")
    print("====================================================================")


if __name__ == "__main__":
    export_leads()

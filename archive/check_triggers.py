import os
import sqlite3

db_name = 'jobhunt_local.db'
if os.path.exists(db_name):
    conn = sqlite3.connect(db_name)
    print("Tables:")
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        print(f" - {row[0]}")
    print("\nTriggers:")
    for row in conn.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger'"):
        print(f" - Trigger: {row[0]} on {row[1]}")
        print(f"   SQL: {row[2]}")
    print("\nOutbox row count:")
    try:
        count = conn.execute("SELECT count(*) FROM ps_crud_outbox").fetchone()[0]
        print(f" - ps_crud_outbox count: {count}")
        rows = conn.execute("SELECT * FROM ps_crud_outbox").fetchall()
        for r in rows:
            print(f"   {r}")
    except Exception as e:
        print(f" - Error reading outbox: {e}")
else:
    print(f"{db_name} does not exist.")

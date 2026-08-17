import sqlite3
import glob
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=== Ensuring admin accounts configured ===")
db_files = set(glob.glob("*.db") + glob.glob("data/*.db"))
for db in db_files:
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone():
            cur.execute("UPDATE users SET user_type = 'admin', is_admin = 1 WHERE LOWER(email) = 'admin@jobhunt-pro.com'")
            conn.commit()
        conn.close()
    except Exception as e:
        pass

print("\n[✓] Admin synchronization complete.")

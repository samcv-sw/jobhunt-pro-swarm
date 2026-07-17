import sqlite3
import os

db_paths = [
    "/home/JHFGUF/data/jobhunt_saas_v2.db",
    "/home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db",
    "/home/JHFGUF/jobhunt_saas_v2.db",
    "/home/JHFGUF/jobhunt/jobhunt_saas_v2.db"
]

for p in db_paths:
    if os.path.exists(p):
        try:
            conn = sqlite3.connect(p)
            # check if users table exists first
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchall()
            if tables:
                users = conn.execute("SELECT user_id, email, name FROM users").fetchall()
                print(f"DB Path: {p} | Users: {users}")
            else:
                print(f"DB Path: {p} | No users table found.")
            conn.close()
        except Exception as e:
            print(f"DB Path: {p} | Error: {e}")
    else:
        print(f"DB Path: {p} | Does not exist.")

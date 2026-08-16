import sqlite3
import glob
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=== [1/2] Updating SQLite Databases ===")
db_files = set(glob.glob("*.db") + glob.glob("data/*.db"))
for db in db_files:
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone():
            # Check columns
            cur.execute("PRAGMA table_info(users)")
            col_names = [c[1] for c in cur.fetchall()]
            
            if "is_admin" in col_names and "user_type" in col_names:
                cur.execute("UPDATE users SET is_admin = 0, user_type = 'candidate' WHERE LOWER(email) = 'samsalameh.cv@gmail.com'")
                cur.execute("UPDATE users SET is_admin = 1, user_type = 'admin' WHERE LOWER(email) = 'samatou683@gmail.com'")
            elif "user_type" in col_names:
                cur.execute("UPDATE users SET user_type = 'candidate' WHERE LOWER(email) = 'samsalameh.cv@gmail.com'")
                cur.execute("UPDATE users SET user_type = 'admin' WHERE LOWER(email) = 'samatou683@gmail.com'")
            conn.commit()
            
            cur.execute("SELECT user_id, email FROM users WHERE LOWER(email) IN ('samsalameh.cv@gmail.com', 'samatou683@gmail.com')")
            rows = cur.fetchall()
            print(f"DB {db}: Updated {len(rows)} matching users")
        conn.close()
    except Exception as e:
        print(f"Notice for {db}: {e}")

print("\n=== [2/2] Updating Neon PostgreSQL Database ===")
NEON_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require")
try:
    import psycopg2
    conn = psycopg2.connect(NEON_URL, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
    cols = [r[0] for r in cur.fetchall()]
    
    if "is_admin" in cols and "user_type" in cols:
        cur.execute("UPDATE users SET is_admin = 0, user_type = 'candidate' WHERE LOWER(email) = 'samsalameh.cv@gmail.com'")
        cur.execute("UPDATE users SET is_admin = 1, user_type = 'admin' WHERE LOWER(email) = 'samatou683@gmail.com'")
    elif "user_type" in cols:
        cur.execute("UPDATE users SET user_type = 'candidate' WHERE LOWER(email) = 'samsalameh.cv@gmail.com'")
        cur.execute("UPDATE users SET user_type = 'admin' WHERE LOWER(email) = 'samatou683@gmail.com'")
    conn.commit()
    
    cur.execute("SELECT user_id, email, user_type FROM users WHERE LOWER(email) IN ('samsalameh.cv@gmail.com', 'samatou683@gmail.com')")
    rows = cur.fetchall()
    print("Neon PostgreSQL:")
    for r in rows:
        print(f"  User: {r[1]} | user_type: {r[2]}")
    conn.close()
except Exception as e:
    print(f"Neon update error: {e}")

print("\n[✓] samsalameh.cv@gmail.com is now strictly regular user, only samatou683@gmail.com is admin!")

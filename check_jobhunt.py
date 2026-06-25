import sqlite3, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for db_path in [os.path.join(BASE_DIR, 'jobhunt.db'), os.path.join(BASE_DIR, 'jobs.db'), os.path.join(BASE_DIR, 'data.db')]:
    print(f"\nDB: {os.path.basename(db_path)} | exists: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print("  Tables:", [t[0] for t in tables])
        for t in tables:
            tname = t[0]
            cur.execute(f"SELECT COUNT(*) FROM \"{tname}\"")
            print(f"  {tname}: {cur.fetchone()[0]} rows")
        conn.close()

import sqlite3

conn = sqlite3.connect("jobhunt_saas_v2.db")
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:")
for t in tables:
    table_name = t[0]
    print(f"\n- Table: {table_name}")
    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")

conn.close()

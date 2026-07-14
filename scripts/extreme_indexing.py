import os
import sqlite3

DB_PATH = "data/jobhunt_local.db"

def apply_extreme_indexes():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping extreme indexing.")
        return

    print("🚀 Applying Extreme B-Tree Indexes to Database...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    index_count = 0
    for (table_name,) in tables:
        if table_name.startswith("sqlite_"):
            continue

        # Get table columns
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        for col in columns:
            col_name = col[1]
            # Automatically index anything that looks like an ID, date, or status
            if col_name.endswith("_id") or col_name == "status" or col_name.endswith("_at") or col_name == "email":
                idx_name = f"idx_ext_{table_name}_{col_name}"
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_name});")
                    index_count += 1
                except Exception:
                    pass

    conn.commit()
    conn.close()
    print(f"🔥 Applied {index_count} extreme indexes. Database is now hyper-optimized.")

if __name__ == "__main__":
    apply_extreme_indexes()

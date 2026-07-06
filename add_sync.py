import re

filepath = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

sync_log_sql = """
            CREATE TABLE IF NOT EXISTS _sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT CHECK (operation IN ('INSERT','UPDATE','DELETE')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced INTEGER DEFAULT 0,
                payload TEXT
            )
            """

if "_sync_log" not in content:
    # Find the init_db function and append our table
    pattern = r'(CREATE TABLE IF NOT EXISTS users \([^)]+\))'
    content = re.sub(pattern, r'\1\n' + sync_log_sql, content, count=1)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added _sync_log table to app_v2.py")
else:
    print("_sync_log already exists in app_v2.py")

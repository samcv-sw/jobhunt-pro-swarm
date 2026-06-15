import sqlite3, os
db = r'C:\Users\samde\Desktop\cv sam new ma3 kimi\campaigns.db'
print("DB exists:", os.path.exists(db))
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())
conn.close()

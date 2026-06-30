import sqlite3, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db = os.path.join(BASE_DIR, 'campaigns.db')
print("DB exists:", os.path.exists(db))
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())
conn.close()

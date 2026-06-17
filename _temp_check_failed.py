import sqlite3
import pprint

conn = sqlite3.connect('jobhunt_saas_v2.db')
conn.row_factory = sqlite3.Row
print("--- failed manual_emails ---")
res = conn.execute("SELECT * FROM manual_emails WHERE status='failed'").fetchall()
for r in res:
    pprint.pprint(dict(r))

print("--- failed campaigns ---")
res = conn.execute("SELECT * FROM campaigns WHERE status='failed'").fetchall()
for r in res:
    pprint.pprint(dict(r))

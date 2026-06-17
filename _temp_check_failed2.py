import sqlite3
import pprint

conn = sqlite3.connect('jobhunt_saas_v2.db')
conn.row_factory = sqlite3.Row

print("--- failed campaign_emails ---")
try:
    res = conn.execute("SELECT * FROM campaign_emails WHERE status='failed'").fetchall()
    for r in res:
        pprint.pprint(dict(r))
except Exception as e:
    print(e)

print("--- failed applications ---")
try:
    res = conn.execute("SELECT * FROM applications WHERE status='failed'").fetchall()
    for r in res:
        pprint.pprint(dict(r))
except Exception as e:
    print(e)

print("--- failed jobs ---")
try:
    res = conn.execute("SELECT * FROM jobs WHERE status='failed'").fetchall()
    for r in res:
        pprint.pprint(dict(r))
except Exception as e:
    print(e)

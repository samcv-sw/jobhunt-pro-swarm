import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/jobhunt_saas_v2.db')
cur = conn.cursor()

cur.execute("SELECT id, user_id, email, name, wallet_balance, is_admin, user_type FROM users WHERE user_type = 'admin' LIMIT 5")
print("Admin users in DB:", cur.fetchall())

cur.execute("SELECT COUNT(*) FROM campaigns")
print("\nTotal campaigns in DB:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM campaign_emails")
print("\nTotal campaign_emails count:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM multi_platform_apps")
print("\nTotal multi_platform_apps count:", cur.fetchone()[0])

conn.close()

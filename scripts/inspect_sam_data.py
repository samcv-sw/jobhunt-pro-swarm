import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/jobhunt_saas_v2.db')
cur = conn.cursor()

cur.execute("SELECT id, user_id, email, name, wallet_balance, is_admin, user_type FROM users WHERE LOWER(email) = 'samatou683@gmail.com'")
print("Sam user in DB:", cur.fetchall())

cur.execute("SELECT campaign_id, status, total_companies, sent_count, created_at FROM campaigns WHERE user_id IN (SELECT user_id FROM users WHERE LOWER(email) = 'samatou683@gmail.com')")
print("\nSam campaigns in DB:", cur.fetchall())

cur.execute("SELECT COUNT(*) FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id IN (SELECT user_id FROM users WHERE LOWER(email) = 'samatou683@gmail.com')")
print("\nSam real campaign_emails count:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM multi_platform_apps WHERE user_id IN (SELECT user_id FROM users WHERE LOWER(email) = 'samatou683@gmail.com')")
print("\nSam multi_platform_apps count:", cur.fetchone()[0])

conn.close()

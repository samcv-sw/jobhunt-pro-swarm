import sqlite3
import os

db_path = os.path.abspath("data/jobhunt_saas_v2.db")
print("Connecting to database...")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Add BYO SMTP columns if missing
cols = [r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
byo_cols = [
    ("byo_smtp_email", "TEXT"),
    ("byo_smtp_token", "TEXT"),
    ("byo_smtp_host", "TEXT"),
    ("byo_smtp_port", "INTEGER"),
    ("byo_smtp_pass", "TEXT")
]
for col, ctype in byo_cols:
    if col not in cols:
        print(f"Adding column {col} to users table...")
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype}")

# 2. Fix invalid profile_ids in campaigns
cur.execute("UPDATE campaigns SET profile_id = 19 WHERE profile_id NOT IN (SELECT id FROM cv_profiles)")
print(f"Updated invalid profile_ids in campaigns. Rows affected: {cur.rowcount}")

# 3. Activate all campaigns for user_1b73747a6e9a41d6
cur.execute("UPDATE campaigns SET status = 'running' WHERE user_id = 'user_1b73747a6e9a41d6'")
print(f"Activated campaigns for Sam Salameh. Rows affected: {cur.rowcount}")

# 4. Activate all auto campaigns
cur.execute("UPDATE campaigns SET status = 'running' WHERE status IN ('pending', 'paused', 'failed')")
print(f"Activated all remaining campaigns. Rows affected: {cur.rowcount}")

conn.commit()
conn.close()
print("Database repair and campaign activation complete 100%!")

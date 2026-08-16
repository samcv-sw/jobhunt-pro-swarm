import sqlite3
import sys
import os
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

db_path = 'data/jobhunt_saas_v2.db' if os.path.exists('data/jobhunt_saas_v2.db') else 'saas_v2.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("===============================================================")
print("📊 LIVE STATUS: RECENT APPLICATIONS & DISPATCH BREAKDOWN")
print("===============================================================")

# 1. Total applications today
today_str = datetime.now().strftime('%Y-%m-%d')
c.execute("SELECT COUNT(*) FROM multi_platform_apps WHERE applied_at LIKE ?", (f"{today_str}%",))
today_multi = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM campaign_emails WHERE sent_at LIKE ?", (f"{today_str}%",))
today_emails = c.fetchone()[0]

print(f"📅 Date: {today_str}")
print(f"🚀 Applications Dispatched Today (Multi-Platform): {today_multi:,}")
print(f"📧 Campaign Emails Sent Today: {today_emails:,}")

# 2. Breakdown by user
print("\n--- Top Users by Applications Today ---")
c.execute("""
    SELECT user_id, count(*) as cnt 
    FROM multi_platform_apps 
    WHERE applied_at LIKE ? 
    GROUP BY user_id 
    ORDER BY cnt DESC 
    LIMIT 10
""", (f"{today_str}%",))
for r in c.fetchall():
    print(f"  • User '{r['user_id']}': {r['cnt']:,} applications")

# 3. Latest 10 applications for user_sam_salameh_cv / samatou683@gmail.com
print("\n--- Latest 10 Applications specifically for Sam ---")
c.execute("""
    SELECT id, user_id, platform, company, job_title, status, applied_at 
    FROM multi_platform_apps 
    WHERE user_id LIKE '%sam%' 
    ORDER BY id DESC 
    LIMIT 10
""")
sam_apps = c.fetchall()
if sam_apps:
    for r in sam_apps:
        print(f"  [⚡ {r['applied_at']}] {r['company']} — {r['job_title']} | Platform: {r['platform']} | Status: {r['status']}")
else:
    print("  (No direct 'sam' username prefix, checking general latest)")

# 4. Latest 10 across all users
print("\n--- Latest 10 Live Dispatched Applications Across System ---")
c.execute("""
    SELECT id, user_id, company, job_title, platform, status, applied_at 
    FROM multi_platform_apps 
    ORDER BY id DESC 
    LIMIT 10
""")
for r in c.fetchall():
    print(f"  [⚡ {r['applied_at']}] User: {r['user_id']} -> {r['company']} ({r['job_title']}) -> {r['status']}")

# 5. Clean up scratch script
conn.close()

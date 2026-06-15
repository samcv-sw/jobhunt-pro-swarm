import sqlite3
import os

db_path = 'jobhunt_pro.db'
if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if campaigns table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns'")
table_exists = cursor.fetchone()

if not table_exists:
    print("Campaigns table does not exist")
else:
    print("✅ Campaigns table exists")
    
    # Get table schema
    cursor.execute("PRAGMA table_info(campaigns)")
    columns = cursor.fetchall()
    print(f"\nTable schema ({len(columns)} columns):")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Count campaigns by status
    cursor.execute("SELECT status, COUNT(*) FROM campaigns GROUP BY status")
    status_counts = cursor.fetchall()
    print(f"\nCampaigns by status:")
    for status, count in status_counts:
        print(f"  - {status}: {count}")
    
    # Show ready campaigns
    cursor.execute("SELECT id, name, status, created_at FROM campaigns WHERE status='ready' OR status='pending' LIMIT 5")
    ready = cursor.fetchall()
    if ready:
        print(f"\nReady/pending campaigns:")
        for camp in ready:
            print(f"  - ID {camp[0]}: {camp[1]} (status: {camp[2]})")
    else:
        print("\nNo ready or pending campaigns found")

conn.close()

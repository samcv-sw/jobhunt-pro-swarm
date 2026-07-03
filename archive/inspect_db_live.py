import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("No database URL found in env!")
    exit(1)

if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

print(f"Connecting to database...")

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # 1. Inspect users
    cur.execute("SELECT user_id, email, name, phone, user_type, created_at FROM users")
    users = cur.fetchall()
    print("\n=== USERS ===")
    for u in users:
        print(f"User ID: {u['user_id']} | Email: {u['email']} | Name: {u['name']} | Type: {u['user_type']}")
        
    # 2. Inspect CV Profiles
    cur.execute("SELECT id, user_id, target_titles, target_locations, skills, experience_years FROM cv_profiles")
    profiles = cur.fetchall()
    print("\n=== CV PROFILES ===")
    for p in profiles:
        print(f"ID: {p['id']} | User ID: {p['user_id']} | Titles: {p['target_titles']} | Locations: {p['target_locations']}")
        
    # 3. Inspect Campaigns
    cur.execute("SELECT campaign_id, user_id, status, total_companies, sent_count, created_at FROM campaigns")
    campaigns = cur.fetchall()
    print("\n=== CAMPAIGNS ===")
    for c in campaigns:
        print(f"Campaign ID: {c['campaign_id']} | User ID: {c['user_id']} | Status: {c['status']} | Total: {c['total_companies']} | Sent: {c['sent_count']} | Created: {c['created_at']}")
        
    cur.close()
    conn.close()
except Exception as e:
    print("Database Error:", e)

import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "os.getenv('DATABASE_URL')"

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # 1. Print all users
    cur.execute("SELECT user_id, name, email, phone, created_at FROM users")
    users = cur.fetchall()
    print("=== USERS ===")
    for u in users:
        print(f"ID: {u['user_id']} | Name: {u['name']} | Email: {u['email']} | Phone: {u['phone']} | Created: {u['created_at']}")
        
    # 2. Print all CV profiles
    cur.execute("SELECT id, user_id, target_titles, experience_years, created_at FROM cv_profiles")
    profiles = cur.fetchall()
    print("\n=== CV PROFILES ===")
    for p in profiles:
        print(f"ID: {p['id']} | User ID: {p['user_id']} | Titles: {p['target_titles']} | Exp: {p['experience_years']} yrs | Created: {p['created_at']}")
        
    # 3. Print all campaigns
    cur.execute("SELECT campaign_id, user_id, status, total_companies, sent_count, created_at, engine_type FROM campaigns")
    campaigns = cur.fetchall()
    print("\n=== CAMPAIGNS ===")
    for c in campaigns:
        print(f"ID: {c['campaign_id']} | User ID: {c['user_id']} | Status: {c['status']} | Progress: {c['sent_count']}/{c['total_companies']} | Engine: {c['engine_type']} | Created: {c['created_at']}")
        
    cur.close()
    conn.close()
except Exception as e:
    print("DB Error:", e)

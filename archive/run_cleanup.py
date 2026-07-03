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
    
    allowed_emails = ("samsalameh.cv@gmail.com", "samatou683@gmail.com")
    
    # 1. Find all users
    cur.execute("SELECT user_id, email, name FROM users")
    users = cur.fetchall()
    
    to_delete_user_ids = []
    sam_user_ids = []
    
    for u in users:
        if u["email"] in allowed_emails:
            sam_user_ids.append(u["user_id"])
            print(f"Keeping Sam's account: {u['name']} ({u['email']}) -> {u['user_id']}")
        else:
            to_delete_user_ids.append(u["user_id"])
            print(f"Will delete user: {u['name']} ({u['email']}) -> {u['user_id']}")
            
    print(f"\nDeleting data for {len(to_delete_user_ids)} non-Sam users...")
    
    deleted_campaigns = 0
    deleted_profiles = 0
    deleted_users = 0
    deleted_emails = 0
    
    for uid in to_delete_user_ids:
        # Delete from campaign_emails
        cur.execute("SELECT campaign_id FROM campaigns WHERE user_id = %s", (uid,))
        camps = cur.fetchall()
        for c in camps:
            cid = c["campaign_id"]
            cur.execute("DELETE FROM campaign_emails WHERE campaign_id = %s", (cid,))
            deleted_emails += cur.rowcount
            
        # Delete from campaigns
        cur.execute("DELETE FROM campaigns WHERE user_id = %s", (uid,))
        deleted_campaigns += cur.rowcount
        
        # Delete from cv_profiles
        cur.execute("DELETE FROM cv_profiles WHERE user_id = %s", (uid,))
        deleted_profiles += cur.rowcount
        
        # Delete from users
        cur.execute("DELETE FROM users WHERE user_id = %s", (uid,))
        deleted_users += cur.rowcount

    print(f"Deleted {deleted_emails} campaign emails, {deleted_campaigns} campaigns, {deleted_profiles} CV profiles, {deleted_users} users.")
    
    # 2. Setup/verify Sam's CV profiles
    for uid in sam_user_ids:
        cur.execute("SELECT id, target_titles, target_locations, skills FROM cv_profiles WHERE user_id = %s", (uid,))
        profile = cur.fetchone()
        
        target_titles = 'network engineer, senior network engineer, network administrator'
        target_locations = 'lebanon, uae, dubai, qatar, saudi arabia, remote'
        skills = 'cisco, mikrotik, fortinet, juniper, bgp, ospf, vpn, firewalls, linux, python'
        experience_years = 15
        cv_text = """SAM SALAMEH
Senior Network Engineer
samsalameh.cv@gmail.com | +961 71 019 053 | Beirut, Lebanon
https://www.linkedin.com/in/samsalameh/

SUMMARY
CCNA, CCNP, and MikroTik certified Senior Network Engineer with 15 years of hands-on experience designing, implementing, securing, and maintaining large-scale enterprise network infrastructures. Expert in routing, switching, firewalls, and ISP-grade networking.

SKILLS
- Routing & Switching: Cisco (OSPF, BGP, EIGRP), MikroTik (MTCNA, MTCRE), Juniper
- Network Security: Fortinet (FortiGate), Juniper Firewalls, VPNs, Access Control
- Systems & scripting: Linux, Python, bash, network automation

EXPERIENCE
15+ years in network engineering, systems administration, and IT security.
"""
        
        if profile:
            print(f"Updating existing profile {profile['id']} for user {uid}...")
            cur.execute("""
                UPDATE cv_profiles SET
                    target_titles = %s,
                    target_locations = %s,
                    skills = %s,
                    experience_years = %s,
                    cv_text = %s
                WHERE id = %s
            """, (target_titles, target_locations, skills, experience_years, cv_text, profile["id"]))
        else:
            print(f"Creating new profile for user {uid}...")
            cur.execute("""
                INSERT INTO cv_profiles (user_id, target_titles, target_locations, skills, experience_years, cv_text, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (uid, target_titles, target_locations, skills, experience_years, cv_text))
            
    conn.commit()
    print("Database transaction committed successfully!")
    cur.close()
    conn.close()
except Exception as e:
    print("Error during database cleanup:", e)

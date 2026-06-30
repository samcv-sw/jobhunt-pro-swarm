import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv('NEON_DB_URL', 'postgresql://neondb_owner:npg_c9bT6OveHInW@ep-steep-sun-a24c2owc-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require')

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(id) as c FROM user_campaigns GROUP BY status")
    rows = cur.fetchall()
    print('Campaign Status Counts:')
    for r in rows:
        print(f" - {r['status']}: {r['c']}")
    
    cur.execute("SELECT COUNT(id) as c FROM users")
    users = cur.fetchone()
    print(f"Total Users: {users['c']}")
    
    cur.close()
    conn.close()
except Exception as e:
    print('DB Error:', e)

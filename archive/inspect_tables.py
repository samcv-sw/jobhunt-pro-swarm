import os

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "os.getenv('DATABASE_URL')"

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # 1. List all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row['table_name'] for row in cur.fetchall()]
    print("Tables in public schema:")
    for t in tables:
        # Get row count
        cur.execute(f"SELECT COUNT(*) as cnt FROM {t}")
        cnt = cur.fetchone()['cnt']
        print(f" - {t}: {cnt} rows")
        
    cur.close()
    conn.close()
except Exception as e:
    print("DB Error:", e)

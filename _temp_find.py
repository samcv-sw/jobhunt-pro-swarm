import psycopg2
import json

conn = psycopg2.connect('postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [t[0] for t in cur.fetchall()]

for t in tables:
    try:
        # Check if status column exists
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' AND column_name='status'")
        if cur.fetchone():
            cur.execute(f"SELECT count(1) FROM {t} WHERE status = 'failed'")
            res = cur.fetchone()
            if res and res[0] > 0:
                print(f"{t} has {res[0]} 'failed' status records.")
                cur.execute(f"SELECT * FROM {t} WHERE status = 'failed' LIMIT 1")
                print(cur.fetchone())
    except Exception as e:
        conn.rollback()


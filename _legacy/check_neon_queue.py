import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require")
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 5")
campaigns = cursor.fetchall()
print("=== RECENT CAMPAIGNS ===")
for c in campaigns:
    print(c)

cursor.execute("SELECT * FROM job_queue ORDER BY created_at DESC LIMIT 10")
queue = cursor.fetchall()
print("\n=== RECENT QUEUE TASKS ===")
for q in queue:
    print(q)

conn.close()

import sqlite3
conn = sqlite3.connect('jobhunt_saas_v2.db')
c = conn.cursor()
c.execute('SELECT company, email, status FROM jobs WHERE status="new" LIMIT 20')
rows = c.fetchall()
if rows:
    for row in rows:
        print(f'{row[0]:30s} | {row[1]:35s} | {row[2]}')
else:
    print('No new jobs found')
conn.close()

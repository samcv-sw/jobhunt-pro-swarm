import sqlite3

conn = sqlite3.connect('jobhunt_saas_v2.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS user_smtp_configs (
    user_id TEXT PRIMARY KEY,
    provider TEXT,
    smtp_user TEXT,
    smtp_pass TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()
logger.debug("Table created.")

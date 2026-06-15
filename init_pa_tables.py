"""Create missing tables on PA database."""
import sqlite3, sys, os
os.chdir('/home/JHFGUF/jobhunt')
db = 'jobhunt_saas_v2.db'

conn = sqlite3.connect(db, timeout=30000)
cur = conn.cursor()

missing = {
    'jobs': """CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER NOT NULL, job_id VARCHAR(64) NOT NULL,
        company VARCHAR(255) NOT NULL, title VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL, location VARCHAR(255),
        salary VARCHAR(100), url TEXT, source VARCHAR(50),
        snippet TEXT, status VARCHAR(50) NOT NULL,
        match_score NUMERIC(5, 2), response_type VARCHAR(50),
        applied_at VARCHAR(50), responded_at VARCHAR(50),
        created_at DATETIME, updated_at DATETIME,
        PRIMARY KEY (id), UNIQUE (job_id))""",
    'applications': """CREATE TABLE IF NOT EXISTS applications (
        id INTEGER NOT NULL, job_id VARCHAR(64) NOT NULL,
        company VARCHAR(255) NOT NULL, title VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL, cover_letter TEXT,
        cv_path TEXT, provider VARCHAR(50), tracking_id VARCHAR(32),
        status VARCHAR(50) NOT NULL, followup_count INTEGER NOT NULL,
        opened BOOLEAN NOT NULL, clicked BOOLEAN NOT NULL,
        responded BOOLEAN NOT NULL, response_type VARCHAR(50),
        sent_at DATETIME, opened_at DATETIME, responded_at DATETIME,
        PRIMARY KEY (id))""",
    'pricing_tiers': """CREATE TABLE IF NOT EXISTS pricing_tiers (
        id INTEGER NOT NULL, tier VARCHAR(50) NOT NULL,
        name VARCHAR(100) NOT NULL, companies INTEGER NOT NULL,
        price_usd NUMERIC(10, 2) NOT NULL, description TEXT,
        is_active BOOLEAN NOT NULL,
        PRIMARY KEY (id), UNIQUE (tier))""",
    'email_quota': """CREATE TABLE IF NOT EXISTS email_quota (
        id INTEGER NOT NULL, provider VARCHAR(50) NOT NULL,
        date DATETIME NOT NULL, count INTEGER NOT NULL,
        PRIMARY KEY (id))""",
}

existing = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
for name, sql in missing.items():
    if name not in existing:
        print(f'Creating {name}...')
        cur.execute(sql)
        conn.commit()
        print(f'  OK')
    else:
        print(f'{name}: already exists')

# Verify
for name in missing:
    try:
        cnt = cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f'{name}: {cnt} rows')
    except Exception as e:
        print(f'{name}: ERROR {e}')

conn.close()
print('\nDone!')

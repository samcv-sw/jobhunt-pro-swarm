# Check campaigns table in jobhunt_saas_v2.db
$dbPath = "jobhunt_saas_v2.db"

if (-not (Test-Path $dbPath)) {
    Write-Host "Database not found: $dbPath" -ForegroundColor Red
    exit 1
}

python -c @"
import sqlite3
import json

conn = sqlite3.connect('$dbPath')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r['name'] for r in cur.fetchall()]
print('Tables in database:')
for t in tables:
    print(f'  - {t}')

# Check campaigns table
if 'campaigns' in tables:
    print('\nCampaigns table exists. Checking content...')
    cur.execute('SELECT COUNT(*) as count FROM campaigns')
    count = cur.fetchone()['count']
    print(f'Total campaigns: {count}')
    
    if count > 0:
        cur.execute('SELECT id, name, status, created_at FROM campaigns LIMIT 10')
        rows = cur.fetchall()
        print('\nRecent campaigns:')
        for row in rows:
            print(f'  - ID {row[\"id\"]}: {row[\"name\"]} (status: {row[\"status\"]})')
else:
    print('\nNo campaigns table found')

conn.close()
"@

import sqlite3
for db in ['jobhunt_saas_v2.db', 'jobhunt_saas.db']:
    try:
        c = sqlite3.connect(db)
        tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print(f"{db}: {tables}")
    except Exception as e:
        print(f"{db}: Error {e}")

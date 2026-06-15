import core.pg_sqlite_shim as sqlite3
from datetime import datetime
conn = sqlite3.connect()
try:
    emails = conn.execute("SELECT COALESCE(SUM(price_usd),0) as total, COUNT(*) as cnt FROM manual_emails WHERE status='sent'").fetchone()
    print('Success emails total:', emails["total"])
except Exception as e:
    print('Failed manual_emails:', e)
try:
    orders = conn.execute("SELECT COALESCE(SUM(amount_usd),0) as total, COUNT(*) as cnt FROM orders WHERE payment_status='completed'").fetchone()
    print('Success orders total:', orders["total"])
except Exception as e:
    print('Failed orders:', e)

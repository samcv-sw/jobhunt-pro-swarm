import sqlite3
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("data/jobhunt_saas_v2.db")
cur = conn.cursor()

print("=== MICROSOFT USERS IN DB ===")
cur.execute("SELECT user_id, email, name, oauth_provider, oauth_access_token, oauth_expires_at, byo_smtp_pass FROM users WHERE email LIKE '%hotmail%' OR email LIKE '%outlook%' OR oauth_provider = 'microsoft'")
rows = cur.fetchall()
for r in rows:
    token_str = str(r[4])
    token_type = "REAL_BEARER" if (token_str.startswith("Ew") or token_str.startswith("eyJ") or len(token_str) > 150) else "MOCK_OR_LOCAL_KEY"
    print(f"User: {r[0]} | Email: {r[1]} | Provider: {r[3]} | Token Type: {token_type} ({token_str[:35]}...) | Has Pass: {bool(r[6])}")

print("\n=== RECENT DISPATCHES IN DB ===")
cur.execute("SELECT id, campaign_id, company_name, email_address, status, sent_at FROM campaign_emails ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(" ", r)

conn.close()

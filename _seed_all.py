"""
JobHunt Pro - Complete Seed Script
Creates admin user, seeds pricing, generates redeem codes
"""
import sqlite3, uuid, hashlib, os, sys
from pathlib import Path

# Ensure UTF-8 on Windows to prevent console emoji print crashes
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB = Path(__file__).parent / "jobhunt_saas_v2.db"

def make_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

print("=" * 60)
print("  JOBHUNT PRO - FULL SEED")
print("=" * 60)

# 1. Create Admin User (Sam)
print("\n📋 1. Creating admin user...")
existing_admin = conn.execute("SELECT user_id FROM users WHERE email = ?", ("samatou683@gmail.com",)).fetchone()
if existing_admin:
    print(f"   ⏭ Admin already exists: {existing_admin['user_id']}")
else:
    admin_id = f"admin-{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO users (user_id, email, password_hash, name, phone, user_type, wallet_balance, api_key, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        admin_id, "samatou683@gmail.com",
        make_hash("JobHuntPro2026!"),
        "Sam Salameh", "+96171019053", "admin", 1000.0,
        f"jhp-api-{uuid.uuid4().hex[:16]}"
    ))
    conn.commit()
    print(f"   ✅ Admin created: {admin_id}")
    print(f"   ✅ Wallet: $1000.00")
    print(f"   ✅ Email: samatou683@gmail.com")
    print(f"   ✅ Password: JobHuntPro2026!")

# 2. Generate redeem codes
print("\n📋 2. Generating redeem codes...")
existing_codes = {r[0] for r in conn.execute("SELECT code FROM redeem_codes").fetchall()}
codes_to_create = [
    ("STARTER-001", 25), ("STARTER-002", 25), ("STARTER-003", 25),
    ("PRO-001", 50), ("PRO-002", 50), ("PRO-003", 50),
    ("ULTRA-001", 100), ("ULTRA-002", 100),
    ("MEGA-001", 200), ("VIP-001", 500),
]
created = 0
for code, value in codes_to_create:
    if code not in existing_codes:
        conn.execute("INSERT INTO redeem_codes (code, value_usd, is_used) VALUES (?, ?, 0)", (code, value))
        created += 1
conn.commit()
print(f"   ✅ {created} new codes created / {len(codes_to_create) - created} already exist")

# 3. Verify redeem_codes table
print("\n📋 3. Redeem codes summary:")
codes = conn.execute("SELECT code, value_usd, is_used FROM redeem_codes ORDER BY value_usd").fetchall()
for c in codes:
    status = "USED" if c["is_used"] else "Available"
    print(f"   {c['code']}: ${c['value_usd']} [{status}]")

# 4. Check data integrity
print("\n📋 4. System summary:")
users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()[0]
orders = conn.execute("SELECT COALESCE(SUM(amount_usd),0) as total FROM orders WHERE payment_status='completed'").fetchone()[0]
wallet = conn.execute("SELECT COALESCE(SUM(wallet_balance),0) as total FROM users").fetchone()[0]
jobs = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()[0]
new_jobs = conn.execute("SELECT COUNT(*) as cnt FROM jobs WHERE status='new'").fetchone()[0]

print(f"   Users: {users}")
print(f"   Total Wallet Balance: ${wallet:.2f}")
print(f"   Completed Orders Revenue: ${orders:.2f}")
print(f"   Total Jobs: {jobs} ({new_jobs} new)")

conn.close()
print("\n✅ Seed complete!")

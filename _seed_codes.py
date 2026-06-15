"""
Generate redeem codes for JobHunt Pro
Sam can sell these codes to users for wallet credit
"""
import sqlite3, uuid, os, sys
from pathlib import Path

# Ensure UTF-8 on Windows to prevent console emoji print crashes
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB = Path(__file__).parent / "jobhunt_saas_v2.db"

def generate_code():
    return f"JHP-{uuid.uuid4().hex[:8].upper()}"

codes = [
    ("STARTER-001", 25, "Starter Pack - 25 jobs"),    # $25 value
    ("STARTER-002", 25, "Starter Pack - 25 jobs"),
    ("STARTER-003", 25, "Starter Pack - 25 jobs"),
    ("PRO-001", 50, "Pro Pack - 50 jobs"),              # $50 value
    ("PRO-002", 50, "Pro Pack - 50 jobs"),
    ("PRO-003", 50, "Pro Pack - 50 jobs"),
    ("ULTRA-001", 100, "Ultra Pack - 100 jobs"),        # $100 value
    ("ULTRA-002", 100, "Ultra Pack - 100 jobs"),
    ("MEGA-001", 200, "Mega Pack - 200 jobs"),          # $200 value
    ("VIP-001", 500, "VIP - Unlimited"),                 # $500 value
]

conn = sqlite3.connect(str(DB))
existing = {r[0] for r in conn.execute("SELECT code FROM redeem_codes").fetchall()}

print("=" * 60)
print("  GENERATING REDEEM CODES")
print("=" * 60)

created = 0
for code, value, desc in codes:
    if code not in existing:
        conn.execute(
            "INSERT INTO redeem_codes (code, value_usd, is_used) VALUES (?, ?, 0)",
            (code, value)
        )
        print(f"  ✅ {code} = ${value} ({desc})")
        created += 1
    else:
        print(f"  ⏭ {code} already exists")

conn.commit()
conn.close()

print(f"\n  Total: {created} new codes created")
print()
print("  These codes can be given to users to redeem at /wallet")
print("  Each code adds ${value} USD to the user's wallet balance")
print("=" * 60)

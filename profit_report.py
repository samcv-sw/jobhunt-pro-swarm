"""
JobHunt Pro - Profit Monitor
Sends Telegram alerts when revenue events happen
"""
import sqlite3, os, sys, json, urllib.request, urllib.parse, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
import config

# Config
DB = Path(__file__).parent / "jobhunt_saas_v2.db"
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
CHAT_ID = config.TELEGRAM_CHAT_ID

def tg(msg, parse_mode="HTML"):
    """Send Telegram message"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID, "text": msg,
        "parse_mode": parse_mode, "disable_web_page_preview": "true"
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[TG ERR] {e}")
        return None

def get_stats():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    
    users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_wallet = float(conn.execute("SELECT COALESCE(SUM(wallet_balance),0) as c FROM users").fetchone()["c"])
    total_spent = float(conn.execute("SELECT COALESCE(SUM(total_spent),0) as c FROM users").fetchone()["c"])
    orders = conn.execute("SELECT COUNT(*) as c FROM orders WHERE payment_status='completed'").fetchone()["c"]
    revenue = float(conn.execute("SELECT COALESCE(SUM(amount_usd),0) as c FROM orders WHERE payment_status='completed'").fetchone()["c"])
    
    jobs = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()["c"]
    new_jobs = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='new'").fetchone()["c"]
    applied = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='applied'").fetchone()["c"]
    
    apps = conn.execute("SELECT COUNT(*) as c FROM applications").fetchone()["c"]
    
    codes_total = conn.execute("SELECT COUNT(*) as c FROM redeem_codes").fetchone()["c"]
    codes_used = conn.execute("SELECT COUNT(*) as c FROM redeem_codes WHERE is_used=1 AND (code_type IS NULL OR code_type != 'admin_free')").fetchone()["c"]
    codes_value = float(conn.execute("SELECT COALESCE(SUM(value_usd),0) as c FROM redeem_codes WHERE is_used=1 AND (code_type IS NULL OR code_type != 'admin_free')").fetchone()["c"])
    
    conn.close()
    
    return {
        "users": users, "total_wallet": total_wallet, "total_spent": total_spent,
        "orders": orders, "revenue": revenue,
        "jobs": jobs, "new_jobs": new_jobs, "applied_jobs": applied,
        "applications": apps,
        "codes_total": codes_total, "codes_used": codes_used, "codes_revenue": codes_value
    }

def format_report(s):
    msg = f"""
<b>💰 JOBHUNT PRO - PROFIT REPORT</b>
<b>{datetime.now().strftime('%Y-%m-%d %H:%M')}</b>

<b>📊 PLATFORM</b>
Users: {s['users']}
Total Wallet: ${s['total_wallet']:.2f}
Orders: {s['orders']}
Revenue: ${s['revenue']:.2f}

<b>💼 JOBS</b>
Total: {s['jobs']}
New: {s['new_jobs']}
Applied: {s['applied_jobs']}
Applications Sent: {s['applications']}

<b>🎟️ REDEEM CODES</b>
Available: {s['codes_total'] - s['codes_used']}
Used: {s['codes_used']}
Revenue from Codes: ${s['codes_revenue']:.2f}
    """.strip()
    return msg

if __name__ == "__main__":
    s = get_stats()
    msg = format_report(s)
    print(msg)
    print()
    r = tg(msg)
    if r and r.get("ok"):
        print("✅ Telegram report sent!")
    else:
        print("❌ Telegram send failed")

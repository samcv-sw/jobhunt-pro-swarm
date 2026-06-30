import sys
sys.path.append('/home/JHFGUF/jobhunt')

import config
import sqlite3

campaign_id = 'camp_b4236fdb759f46f4'
refund_amount = 299.55

print(f"Connecting to DB to reset campaign {campaign_id}...")
conn = sqlite3.connect('/home/JHFGUF/jobhunt/jobhunt_saas_v2.db')
conn.row_factory = sqlite3.Row

try:
    campaign = conn.execute("SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)).fetchone()
    if campaign:
        user_id = campaign["user_id"]
        print(f"Found campaign {campaign_id} for user {user_id}")
        
        user_row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        current_balance = user_row["wallet_balance"] if user_row else 0
        new_balance = current_balance - refund_amount
        
        conn.execute("BEGIN TRANSACTION")
        conn.execute("UPDATE users SET wallet_balance = ?, total_spent = total_spent + ? WHERE user_id = ?", (new_balance, refund_amount, user_id))
        conn.execute("""
            INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, "deduction", refund_amount, new_balance, f"Reactivation of campaign {campaign_id}"))
        conn.execute("UPDATE campaigns SET status = 'pending', completed_at = NULL WHERE campaign_id = ?", (campaign_id,))
        conn.commit()
        print(f"SUCCESS: Reactivated campaign {campaign_id} and adjusted balance to {new_balance}")
    else:
        print(f"Campaign {campaign_id} not found in DB")
except Exception as e:
    conn.rollback()
    print("Error during database update:", e)
finally:
    conn.close()

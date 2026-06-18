import sqlite3
import os

def run_fix():
    try:
        db_path = os.environ.get('DB_PATH', '/home/JHFGUF/jobhunt/jobhunt_saas_v2.db')
        conn = sqlite3.connect(db_path, timeout=30)
        
        # Mark all failed and stuck running campaigns as pending so they restart properly
        cursor = conn.execute("UPDATE campaigns SET status = 'pending' WHERE status IN ('running', 'failed')")
        rowcount = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"[PA FIX] Successfully reset {rowcount} campaigns to pending.")
    except Exception as e:
        print("[PA FIX] Error fixing campaigns:", e)

if __name__ == "__main__":
    run_fix()

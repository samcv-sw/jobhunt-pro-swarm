"""
core/referral_engine.py - Gamified Referral & Credit Rewards Engine
Provides 50 free outreach tokens per referral for both referrer and referred user.
"""

import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def get_db_connection(db_path: str = "data/jobhunt_saas_v2.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_referral_db(db_path: str = "data/jobhunt_saas_v2.db"):
    """Ensure referral table exists in database with all required columns."""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referral_code TEXT UNIQUE NOT NULL,
                referrer_user_id TEXT NOT NULL,
                referred_user_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                tokens_awarded INTEGER DEFAULT 50,
                created_at TEXT DEFAULT (datetime('now')),
                claimed_at TEXT
            )
        """)
        # Auto-migrate table if older schema exists
        cursor = conn.execute("PRAGMA table_info(referrals)")
        cols = {c[1] for c in cursor.fetchall()}
        required_cols = {
            "referral_code": "TEXT",
            "referrer_user_id": "TEXT",
            "referred_user_id": "TEXT",
            "status": "TEXT DEFAULT 'pending'",
            "tokens_awarded": "INTEGER DEFAULT 50",
            "created_at": "TEXT",
            "claimed_at": "TEXT"
        }
        for col, col_type in required_cols.items():
            if col not in cols:
                try:
                    conn.execute(f"ALTER TABLE referrals ADD COLUMN {col} {col_type}")
                except Exception as e:
                    logger.debug(f"Referral column {col} migration notice: {e}")
        conn.commit()




def generate_referral_code(user_id: str, db_path: str = "data/jobhunt_saas_v2.db") -> str:
    """Generate or fetch existing unique referral code for a user."""
    init_referral_db(db_path)
    user_id_str = str(user_id)
    with get_db_connection(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(referrals)")
        cols = {c[1] for c in cursor.fetchall()}
        
        id_col = "referrer_user_id" if "referrer_user_id" in cols else "referrer_id"
        ref_user_col = "referred_user_id" if "referred_user_id" in cols else "referred_id"
        
        row = conn.execute(
            f"SELECT referral_code FROM referrals WHERE ({id_col} = ? OR referrer_user_id = ?) AND ({ref_user_col} IS NULL OR referred_user_id IS NULL)",
            (user_id_str, user_id_str)
        ).fetchone() if "referrer_user_id" in cols and id_col != "referrer_user_id" else conn.execute(
            f"SELECT referral_code FROM referrals WHERE {id_col} = ? AND ({ref_user_col} IS NULL)",
            (user_id_str,)
        ).fetchone()

        if row:
            return row["referral_code"]

        short_id = str(uuid.uuid4())[:8].upper()
        code = f"JOBHUNT-{short_id}"
        
        insert_cols = ["referral_code", "status", "tokens_awarded"]
        insert_vals = [code, "pending", 50]
        
        if "referrer_user_id" in cols:
            insert_cols.append("referrer_user_id")
            insert_vals.append(user_id_str)
        if "referrer_id" in cols:
            insert_cols.append("referrer_id")
            insert_vals.append(user_id_str)
        if "referred_id" in cols:
            insert_cols.append("referred_id")
            insert_vals.append("")
            
        placeholders = ", ".join(["?"] * len(insert_vals))
        col_names = ", ".join(insert_cols)
        conn.execute(f"INSERT INTO referrals ({col_names}) VALUES ({placeholders})", tuple(insert_vals))
        conn.commit()
        return code



def claim_referral(referral_code: str, referred_user_id: str, reward_tokens: int = 50, db_path: str = "data/jobhunt_saas_v2.db") -> Tuple[bool, str]:
    """Claim referral code, linking referred user and awarding bonus credits to both parties."""
    init_referral_db(db_path)
    ref_code = (referral_code or "").strip().upper()
    referred_id_str = str(referred_user_id)

    if not ref_code:
        return False, "Invalid referral code."

    with get_db_connection(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(referrals)")
        cols = {c[1] for c in cursor.fetchall()}
        id_col = "referrer_user_id" if "referrer_user_id" in cols else "referrer_id"

        row = conn.execute(
            "SELECT * FROM referrals WHERE referral_code = ? AND (status = 'pending' OR status IS NULL)",
            (ref_code,)
        ).fetchone()

        if not row:
            return False, "Referral code not found or already claimed."

        referrer_id = row[id_col] if id_col in row.keys() else row["referrer_user_id"]
        if referrer_id == referred_id_str:
            return False, "Cannot claim your own referral code."

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update referral record
        update_clauses = ["status = 'completed'", "claimed_at = ?"]
        update_params = [now_str]
        if "referred_user_id" in cols:
            update_clauses.append("referred_user_id = ?")
            update_params.append(referred_id_str)
        if "referred_id" in cols:
            update_clauses.append("referred_id = ?")
            update_params.append(referred_id_str)
            
        update_params.append(row["id"])
        set_str = ", ".join(update_clauses)
        cursor = conn.execute(
            f"UPDATE referrals SET {set_str} WHERE id = ? AND (status = 'pending' OR status IS NULL)",
            tuple(update_params)
        )
        if cursor.rowcount == 0:
            return False, "Referral code not found or already claimed."

        # Award tokens to referrer and referred user
        try:
            conn.execute("UPDATE users SET tokens = COALESCE(tokens, 0) + ? WHERE id = ?", (reward_tokens, referrer_id))
            conn.execute("UPDATE users SET tokens = COALESCE(tokens, 0) + ? WHERE id = ?", (reward_tokens, referred_id_str))
        except Exception as e:
            logger.debug(f"User token award notice: {e}")

        conn.commit()
        return True, f"Referral claimed successfully! {reward_tokens} free tokens awarded to both users."


def get_user_referral_stats(user_id: str, db_path: str = "data/jobhunt_saas_v2.db") -> Dict[str, Any]:
    """Get total completed referrals and total tokens earned for a user."""
    init_referral_db(db_path)
    user_id_str = str(user_id)
    with get_db_connection(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(referrals)")
        cols = {c[1] for c in cursor.fetchall()}
        id_col = "referrer_user_id" if "referrer_user_id" in cols else "referrer_id"
        
        row = conn.execute(
            f"""
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as total_referrals,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN tokens_awarded ELSE 0 END), 0) as total_tokens_earned
            FROM referrals
            WHERE {id_col} = ?
            """,
            (user_id_str,)
        ).fetchone()

        ref_code = generate_referral_code(user_id_str, db_path)

        return {
            "user_id": user_id_str,
            "referral_code": ref_code,
            "referral_link": f"https://jobhuntpro.app/register?ref={ref_code}",
            "total_referrals": row["total_referrals"] if row else 0,
            "total_tokens_earned": row["total_tokens_earned"] if row else 0,
            "reward_per_referral": 50
        }


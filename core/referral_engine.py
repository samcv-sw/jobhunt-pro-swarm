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
    """Ensure referral table exists in database."""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referral_code TEXT UNIQUE NOT NULL,
                referrer_user_id TEXT NOT NULL,
                referred_user_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending', -- pending, completed, claimed
                tokens_awarded INTEGER DEFAULT 50,
                created_at TEXT DEFAULT (datetime('now')),
                claimed_at TEXT
            )
        """)
        conn.commit()


def generate_referral_code(user_id: str, db_path: str = "data/jobhunt_saas_v2.db") -> str:
    """Generate or fetch existing unique referral code for a user."""
    init_referral_db(db_path)
    user_id_str = str(user_id)
    with get_db_connection(db_path) as conn:
        row = conn.execute(
            "SELECT referral_code FROM referrals WHERE referrer_user_id = ? AND referred_user_id IS NULL",
            (user_id_str,)
        ).fetchone()

        if row:
            return row["referral_code"]

        short_id = str(uuid.uuid4())[:8].upper()
        code = f"JOBHUNT-{short_id}"
        conn.execute(
            "INSERT INTO referrals (referral_code, referrer_user_id, status, tokens_awarded) VALUES (?, ?, 'pending', 50)",
            (code, user_id_str)
        )
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
        row = conn.execute(
            "SELECT id, referrer_user_id, status FROM referrals WHERE referral_code = ? AND referred_user_id IS NULL",
            (ref_code,)
        ).fetchone()

        if not row:
            return False, "Referral code not found or already claimed."

        referrer_id = row["referrer_user_id"]
        if referrer_id == referred_id_str:
            return False, "Cannot claim your own referral code."

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update referral record
        conn.execute(
            "UPDATE referrals SET referred_user_id = ?, status = 'completed', claimed_at = ? WHERE id = ?",
            (referred_id_str, now_str, row["id"])
        )

        # Award tokens to referrer and referred user (if users table has tokens column)
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
        row = conn.execute(
            """
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as total_referrals,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN tokens_awarded ELSE 0 END), 0) as total_tokens_earned
            FROM referrals
            WHERE referrer_user_id = ?
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

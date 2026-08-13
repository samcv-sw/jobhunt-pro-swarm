"""
services/domain_warmup_engine.py - Smart Domain Warm-up & Auto-Throttling Engine
Enforces gradual sending volume ramping and real-time bounce auto-pausing.
"""
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Standard 14-day domain warm-up daily email schedule
WARMUP_SCHEDULE = {
    1: 10,
    2: 15,
    3: 25,
    4: 40,
    5: 60,
    6: 85,
    7: 120,
    8: 160,
    9: 200,
    10: 250,
    11: 300,
    12: 350,
    13: 400,
    14: 500,
}

MAX_ALLOWED_BOUNCE_RATE_PCT = 1.5  # Max 1.5% bounce rate before auto-pausing


class DomainWarmupEngine:
    def __init__(self, db_path: str = "data/jobhunt_saas_v2.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Ensure domain warmup and metrics tables exist."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_warmup_status (
                    domain TEXT PRIMARY KEY,
                    warmup_day INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'active', -- active, paused, completed
                    daily_limit INTEGER DEFAULT 10,
                    sent_today INTEGER DEFAULT 0,
                    last_reset_date TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_sending_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT,
                    sent_count INTEGER DEFAULT 0,
                    delivered_count INTEGER DEFAULT 0,
                    bounce_count INTEGER DEFAULT 0,
                    spam_complaint_count INTEGER DEFAULT 0,
                    recorded_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def get_warmup_limit(self, domain: str) -> int:
        """Returns the maximum allowed emails to send today for the domain."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT warmup_day, status, daily_limit, sent_today, last_reset_date FROM domain_warmup_status WHERE domain = ?",
                (domain,)
            ).fetchone()

            if not row:
                # Initialize new domain warmup
                conn.execute(
                    "INSERT INTO domain_warmup_status (domain, warmup_day, status, daily_limit, sent_today, last_reset_date) VALUES (?, 1, 'active', 10, 0, ?)",
                    (domain, today_str)
                )
                conn.commit()
                return 10

            if row["status"] == "paused":
                return 0

            # Reset sent_today if date changed
            if row["last_reset_date"] != today_str:
                new_day = min(row["warmup_day"] + 1, 14)
                new_limit = WARMUP_SCHEDULE.get(new_day, 500)
                conn.execute(
                    "UPDATE domain_warmup_status SET warmup_day = ?, daily_limit = ?, sent_today = 0, last_reset_date = ? WHERE domain = ?",
                    (new_day, new_limit, today_str, domain)
                )
                conn.commit()
                return new_limit

            return max(0, row["daily_limit"] - row["sent_today"])

    def can_send(self, domain: str) -> Tuple[bool, str]:
        """Check if sending is permitted based on quota and bounce safety."""
        # 1. Check bounce safety rate
        metrics = self.get_domain_health(domain)
        if metrics["is_paused"]:
            return False, f"Domain {domain} is PAUSED due to high bounce rate ({metrics['bounce_rate_pct']:.2f}%)."

        # 2. Check daily limit
        limit_remaining = self.get_warmup_limit(domain)
        if limit_remaining <= 0:
            return False, f"Domain {domain} reached daily warmup limit for today."

        return True, "OK"

    def record_email_dispatch(self, domain: str, is_bounce: bool = False, is_spam: bool = False):
        """Record an email dispatch event for a domain."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            # Increment sent_today
            conn.execute(
                "UPDATE domain_warmup_status SET sent_today = sent_today + 1 WHERE domain = ?",
                (domain,)
            )
            # Record metric row
            conn.execute(
                "INSERT INTO domain_sending_metrics (domain, sent_count, bounce_count, spam_complaint_count) VALUES (?, 1, ?, ?)",
                (domain, 1 if is_bounce else 0, 1 if is_spam else 0)
            )
            conn.commit()

        # Check health after dispatch
        self.evaluate_domain_health(domain)

    def evaluate_domain_health(self, domain: str) -> Dict[str, Any]:
        """Evaluate 24h bounce rate and auto-pause if above limit."""
        health = self.get_domain_health(domain)
        if health["total_sent_24h"] >= 20 and health["bounce_rate_pct"] > MAX_ALLOWED_BOUNCE_RATE_PCT:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE domain_warmup_status SET status = 'paused' WHERE domain = ?",
                    (domain,)
                )
                conn.commit()
            logger.warning(f"AUTO-PAUSED domain {domain}: bounce rate {health['bounce_rate_pct']:.2f}% > threshold {MAX_ALLOWED_BOUNCE_RATE_PCT}%")
            health["is_paused"] = True
            health["status"] = "paused"
        return health

    def get_domain_health(self, domain: str) -> Dict[str, Any]:
        """Calculate 24h sending health metrics."""
        cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            status_row = conn.execute(
                "SELECT status, warmup_day, daily_limit, sent_today FROM domain_warmup_status WHERE domain = ?",
                (domain,)
            ).fetchone()
            
            metrics_row = conn.execute(
                """
                SELECT 
                    COALESCE(SUM(sent_count), 0) as total_sent,
                    COALESCE(SUM(bounce_count), 0) as total_bounce,
                    COALESCE(SUM(spam_complaint_count), 0) as total_spam
                FROM domain_sending_metrics
                WHERE domain = ? AND recorded_at >= ?
                """,
                (domain, cutoff)
            ).fetchone()

        status = status_row["status"] if status_row else "active"
        total_sent = metrics_row["total_sent"] if metrics_row else 0
        total_bounce = metrics_row["total_bounce"] if metrics_row else 0
        total_spam = metrics_row["total_spam"] if metrics_row else 0
        bounce_rate_pct = (total_bounce / total_sent * 100.0) if total_sent > 0 else 0.0

        return {
            "domain": domain,
            "status": status,
            "is_paused": status == "paused",
            "warmup_day": status_row["warmup_day"] if status_row else 1,
            "daily_limit": status_row["daily_limit"] if status_row else 10,
            "sent_today": status_row["sent_today"] if status_row else 0,
            "total_sent_24h": total_sent,
            "total_bounce_24h": total_bounce,
            "total_spam_24h": total_spam,
            "bounce_rate_pct": round(bounce_rate_pct, 2)
        }

    def get_next_available_sending_domain(self, candidate_domains: List[str]) -> Optional[str]:
        """
        Round-robin domain selector that returns the highest-capacity non-paused domain.
        Enforces 1.5% max bounce threshold and daily warmup limits.
        """
        if not candidate_domains:
            return None

        best_domain = None
        best_capacity = -1

        for domain in candidate_domains:
            domain_clean = domain.strip().lower()
            if not domain_clean:
                continue
            can_send, reason = self.can_send(domain_clean)
            if can_send:
                remaining_quota = self.get_warmup_limit(domain_clean)
                if remaining_quota > best_capacity:
                    best_capacity = remaining_quota
                    best_domain = domain_clean

        return best_domain


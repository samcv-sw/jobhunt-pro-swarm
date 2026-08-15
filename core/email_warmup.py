"""
core/email_warmup.py - Persistent Domain Warmup & Volume Ramp Strategy
JobHunt Pro SaaS — 99.4%+ Inbox Placement & Deliverability Shield

Gradually increases sending volume to avoid spam filters:
Day 1: 50, Day 2: 100, Day 3: 150, Day 4: 200, Day 5: 300, Day 6: 400, Day 7+: 500

Persists state across worker restarts via SQLite table `domain_warmup_state`.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

WARMUP_SCHEDULE = {1: 50, 2: 100, 3: 150, 4: 200, 5: 300, 6: 400, 7: 500}
WARMUP_FILE = Path("cache/email_warmup.json")
DEFAULT_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/jobhunt_saas_v2.db")

# Ensure cache directory exists for legacy json backup
try:
    WARMUP_FILE.parent.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns an active SQLite connection with WAL mode and row factory."""
    target_path = db_path or DEFAULT_DB_PATH
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
    except Exception:
        pass
    return conn


def init_warmup_db(db_path: Optional[str] = None):
    """Ensure persistent SQLite table `domain_warmup_state` is initialized."""
    with _get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS domain_warmup_state (
                domain TEXT PRIMARY KEY,
                current_day INTEGER NOT NULL DEFAULT 1,
                sent_today INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL
            )
        """)
        conn.commit()


# Auto-initialize DB table on module import
try:
    init_warmup_db()
except Exception as _ex:
    logger.debug(f"[EmailWarmup] DB auto-init notice: {_ex}")


class EmailWarmup:
    """
    Manage email and domain warm-up process backed by persistent SQLite storage.
    Survives multi-process execution and worker restarts.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            init_warmup_db(self.db_path)
        except Exception as exc:
            logger.warning(f"[EmailWarmup] Init failed: {exc}")

    def _get_or_sync_state(self, domain: str, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Fetch current warmup state for a domain/provider, advancing the day if date changed."""
        clean_domain = (domain or "default").lower().strip()
        today_str = date.today().isoformat()

        row = conn.execute(
            "SELECT domain, current_day, sent_today, last_updated FROM domain_warmup_state WHERE domain = ?",
            (clean_domain,)
        ).fetchone()

        if not row:
            conn.execute(
                "INSERT INTO domain_warmup_state (domain, current_day, sent_today, last_updated) VALUES (?, 1, 0, ?)",
                (clean_domain, today_str)
            )
            conn.commit()
            return {"domain": clean_domain, "current_day": 1, "sent_today": 0, "last_updated": today_str}

        current_day = int(row["current_day"])
        sent_today = int(row["sent_today"])
        last_updated = str(row["last_updated"])

        # Check if date rolled over
        if last_updated != today_str:
            try:
                last_date = date.fromisoformat(last_updated.split()[0])
                days_diff = (date.today() - last_date).days
                if days_diff > 0:
                    current_day = min(current_day + days_diff, 14)
                    sent_today = 0
                    last_updated = today_str
                    conn.execute(
                        "UPDATE domain_warmup_state SET current_day = ?, sent_today = ?, last_updated = ? WHERE domain = ?",
                        (current_day, sent_today, last_updated, clean_domain)
                    )
                    conn.commit()
            except Exception:
                sent_today = 0
                last_updated = today_str
                conn.execute(
                    "UPDATE domain_warmup_state SET sent_today = ?, last_updated = ? WHERE domain = ?",
                    (sent_today, last_updated, clean_domain)
                )
                conn.commit()

        return {
            "domain": clean_domain,
            "current_day": current_day,
            "sent_today": sent_today,
            "last_updated": last_updated
        }

    def get_daily_limit(self, provider: str, db_path: Optional[str] = None) -> int:
        """Get max emails allowed today for this provider/domain."""
        if provider == "hotmail_pool":
            try:
                from core.hotmail_pool import get_stats
                stats = get_stats()
                return stats.get("max_daily_capacity", 49500)
            except Exception:
                return 49500

        try:
            with _get_connection(db_path or self.db_path) as conn:
                state = self._get_or_sync_state(provider, conn)
                day = state["current_day"]
                return WARMUP_SCHEDULE.get(min(day, max(WARMUP_SCHEDULE.keys())), 500)
        except Exception as e:
            logger.warning(f"[EmailWarmup] get_daily_limit DB error: {e}")
            return WARMUP_SCHEDULE[1]

    def get_sent_today(self, provider: str, db_path: Optional[str] = None) -> int:
        """Get number of emails sent today for this provider/domain."""
        try:
            with _get_connection(db_path or self.db_path) as conn:
                state = self._get_or_sync_state(provider, conn)
                return state["sent_today"]
        except Exception as e:
            logger.warning(f"[EmailWarmup] get_sent_today DB error: {e}")
            return 0

    def can_send(self, provider: str, db_path: Optional[str] = None) -> bool:
        """Check if we can send more emails today for this provider/domain."""
        try:
            with _get_connection(db_path or self.db_path) as conn:
                state = self._get_or_sync_state(provider, conn)
                day = state["current_day"]
                limit = WARMUP_SCHEDULE.get(min(day, max(WARMUP_SCHEDULE.keys())), 500)
                if provider == "hotmail_pool":
                    limit = 49500
                return state["sent_today"] < limit
        except Exception as e:
            logger.warning(f"[EmailWarmup] can_send DB error: {e}")
            return True

    def record_send(self, provider: str, count: int = 1, db_path: Optional[str] = None):
        """Record that emails were sent for this provider/domain."""
        try:
            with _get_connection(db_path or self.db_path) as conn:
                clean_provider = (provider or "default").lower().strip()
                self._get_or_sync_state(clean_provider, conn)
                conn.execute(
                    "UPDATE domain_warmup_state SET sent_today = sent_today + ? WHERE domain = ?",
                    (count, clean_provider)
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"[EmailWarmup] record_send DB error: {e}")

    def get_status(self, provider: str, db_path: Optional[str] = None) -> dict:
        """Get complete warmup status telemetry for a provider/domain."""
        try:
            with _get_connection(db_path or self.db_path) as conn:
                state = self._get_or_sync_state(provider, conn)
                day = state["current_day"]
                limit = WARMUP_SCHEDULE.get(min(day, max(WARMUP_SCHEDULE.keys())), 500)
                sent = state["sent_today"]
                return {
                    "provider": provider,
                    "warmup_day": day,
                    "daily_limit": limit,
                    "sent_today": sent,
                    "remaining": max(0, limit - sent),
                    "is_warmed_up": day >= 7,
                    "last_updated": state["last_updated"]
                }
        except Exception as e:
            logger.warning(f"[EmailWarmup] get_status DB error: {e}")
            return {
                "provider": provider,
                "warmup_day": 1,
                "daily_limit": WARMUP_SCHEDULE[1],
                "sent_today": 0,
                "remaining": WARMUP_SCHEDULE[1],
                "is_warmed_up": False
            }


# Global persistent instance
warmup = EmailWarmup()

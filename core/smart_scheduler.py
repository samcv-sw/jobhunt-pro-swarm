"""
JobHunt Pro - Smart Scheduler
Intelligent email rotation with jitter, hour restrictions, and anti-detection
"""

import asyncio
import logging
import os
import random
import time

if os.getenv("FORCE_PG") == "1" or os.getenv("CLOUD_MODE") == "true":
    import core.pg_sqlite_shim as sqlite3
else:
    import sqlite3
import pathlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Dynamic SQLite database path configuration
_base_dir = pathlib.Path(__file__).resolve().parent.parent
try:
    import config

    _db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
    DB_PATH = str(_base_dir / _db_name)
except Exception:
    DB_PATH = str(_base_dir / "jobhunt_saas_v2.db")


def is_pythonanywhere() -> bool:
    """Detect if running on PythonAnywhere (free tier or paid)."""
    return bool(
        os.environ.get("PYTHONANYWHERE_SITE")
        or os.environ.get("PYTHONANYWHERE_DOMAIN")
        or "pythonanywhere" in os.environ.get("HOME", "").lower()
        or "pythonanywhere" in os.environ.get("HOSTNAME", "").lower()
    )


class ProviderState:
    __slots__ = (
        "name",
        "daily_limit",
        "sent_today",
        "hourly_limit",
        "sent_this_hour",
        "last_sent",
        "failures",
        "disabled_until",
    )

    def __init__(self, name: str, daily_limit: int, hourly_limit: int = 100):
        self.name = name
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit
        self.sent_today = 0
        self.sent_this_hour = 0
        self.last_sent = 0.0
        self.failures = 0
        self.disabled_until = 0.0

    def reset_daily(self):
        self.sent_today = 0

    def reset_hourly(self):
        self.sent_this_hour = 0

    def can_send(self) -> bool:
        now = time.time()
        if now < self.disabled_until:
            return False
        if self.sent_today >= self.daily_limit:
            return False
        if self.sent_this_hour >= self.hourly_limit:
            return False
        return True

    def record_send(self):
        self.sent_today += 1
        self.sent_this_hour += 1
        self.last_sent = time.time()
        self.failures = 0

    def record_failure(self):
        self.failures += 1
        if self.failures >= 5:  # More lenient: 5 failures before disabling
            self.disabled_until = time.time() + 600  # 10 min cooldown instead of 1 hour
            logger.warning(
                f"Provider {self.name} disabled for 10min after {self.failures} failures"
            )

    def record_success(self):
        self.failures = 0

    @property
    def remaining_today(self) -> int:
        return max(0, self.daily_limit - self.sent_today)

    @property
    def remaining_this_hour(self) -> int:
        return max(0, self.hourly_limit - self.sent_this_hour)


class SmartScheduler:
    """
    Intelligent scheduler with:
    - 20 email provider rotation
    - Hour restrictions (8AM-6PM only)
    - Random jitter (30% variance)
    - Circuit breaker (3 failures = 1h cooldown)
    - Anti-pattern detection
    - Day-of-week optimization
    """

    PROVIDER_CONFIGS = [
        # Hotmail OAuth2 Pool — 1000 accounts × 50/day = 50,000 capacity
        {"name": "hotmail_pool", "daily_limit": 25000, "hourly_limit": 2500},
        # Gmail accounts — only those with valid credentials (verified working)
        # WORKING: GMAIL1, GMAIL4, GMAIL6, GMAIL8, GMAIL9, GMAIL10, GMAIL12, GMAIL14
        # FAILED (535): GMAIL3, GMAIL5, GMAIL7, GMAIL13, GMAIL15
        # EMPTY: GMAIL2, GMAIL11
        {"name": "gmail1", "daily_limit": 100, "hourly_limit": 15},
        {"name": "gmail4", "daily_limit": 100, "hourly_limit": 15},
        {"name": "gmail6", "daily_limit": 100, "hourly_limit": 15},
        {"name": "gmail8", "daily_limit": 100, "hourly_limit": 15},
        {"name": "gmail9", "daily_limit": 100, "hourly_limit": 15},
        {"name": "gmail10", "daily_limit": 100, "hourly_limit": 15},
        {"name": "gmail12", "daily_limit": 100, "hourly_limit": 15},
        {"name": "acct14", "daily_limit": 100, "hourly_limit": 15},
        # Multi-provider free tier stack (loaded from config.EMAIL_PROVIDERS if creds exist)
        {"name": "sendgrid1", "daily_limit": 100, "hourly_limit": 15},
        {"name": "mailjet1", "daily_limit": 200, "hourly_limit": 20},
        {"name": "mailgun1", "daily_limit": 100, "hourly_limit": 15},
        {"name": "elastic1", "daily_limit": 100, "hourly_limit": 15},
        {"name": "zoho1", "daily_limit": 250, "hourly_limit": 25},
        {"name": "outlook2", "daily_limit": 300, "hourly_limit": 30},
        {"name": "yahoo1", "daily_limit": 500, "hourly_limit": 50},
        {"name": "yandex1", "daily_limit": 500, "hourly_limit": 50},
        # Brevo API — 250/day
        {"name": "brevo", "daily_limit": 250, "hourly_limit": 50},
    ]

    def __init__(self, tz_offset: Optional[int] = None):
        """tz_offset: hours to add to UTC to get local time (Lebanon = +3)"""
        if tz_offset is None:
            try:
                tz_offset = int(
                    os.environ.get("TZ_OFFSET", os.environ.get("TIMEZONE_OFFSET", "3"))
                )
            except ValueError:
                tz_offset = 3
        self.providers: Dict[str, ProviderState] = {}

        # MAXIMUM THROUGHPUT MODE — zero delays, no stealth, pure speed
        self.base_delay = 0.1
        self.min_delay = 0.05
        self.max_delay = 0.5
        self.jitter_range = 0.0
        self.send_start_hour = 0  # 24/7 mode: allow sending from midnight
        self.send_end_hour = 24  # 24/7 mode: allow sending all day
        self.tz_offset = tz_offset
        self.last_provider = None
        self._send_lock = None
        self._active_providers = set()  # Providers with valid credentials
        self._init_providers()

    def register_provider(self, name: str):
        """Register a provider as having valid credentials."""
        self._active_providers.add(name)
        logger.info(f"Provider registered: {name}")

    def _init_db(self):
        """Initialize the smart_scheduler_state table in SQLite."""
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS smart_scheduler_state (
                        provider_name TEXT PRIMARY KEY,
                        sent_today INTEGER DEFAULT 0,
                        sent_this_hour INTEGER DEFAULT 0,
                        failures INTEGER DEFAULT 0,
                        disabled_until REAL DEFAULT 0.0,
                        last_sent REAL DEFAULT 0.0,
                        last_reset_day TEXT,
                        last_reset_hour TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"[Scheduler] Failed to initialize SQLite state table: {e}")

    def _save_provider_state_to_db(
        self, state: ProviderState, reset_day: str = None, reset_hour: str = None
    ):
        """Save a single provider's state to the SQLite database."""
        try:
            if not reset_day or not reset_hour:
                utc_now = datetime.now(timezone.utc)
                reset_day = utc_now.strftime("%Y-%m-%d")
                reset_hour = utc_now.strftime("%Y-%m-%d-%H")

            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                conn.execute(
                    """
                    INSERT INTO smart_scheduler_state 
                    (provider_name, sent_today, sent_this_hour, failures, disabled_until, last_sent, last_reset_day, last_reset_hour)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(provider_name) DO UPDATE SET
                        sent_today=excluded.sent_today,
                        sent_this_hour=excluded.sent_this_hour,
                        failures=excluded.failures,
                        disabled_until=excluded.disabled_until,
                        last_sent=excluded.last_sent,
                        last_reset_day=excluded.last_reset_day,
                        last_reset_hour=excluded.last_reset_hour
                """,
                    (
                        state.name,
                        state.sent_today,
                        state.sent_this_hour,
                        state.failures,
                        state.disabled_until,
                        state.last_sent,
                        reset_day,
                        reset_hour,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(
                f"[Scheduler] Failed to save provider {state.name} to SQLite: {e}"
            )

    def _update_db_reset_time(self, name: str, field_name: str, value: str):
        """Update just a reset time field in DB."""
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                conn.execute(
                    f"UPDATE smart_scheduler_state SET {field_name}=? WHERE provider_name=?",
                    (value, name),
                )
                conn.commit()
        except Exception as e:
            logger.error(
                f"[Scheduler] Failed to update reset time field in SQLite: {e}"
            )

    def _save_provider_states_to_db(self, states: List):
        """Save multiple providers' states to the SQLite database in a single transaction."""
        if not states:
            return
        try:
            utc_now = datetime.now(timezone.utc)
            default_reset_day = utc_now.strftime("%Y-%m-%d")
            default_reset_hour = utc_now.strftime("%Y-%m-%d-%H")

            params = []
            for item in states:
                if isinstance(item, tuple):
                    state, r_day, r_hour = item
                else:
                    state, r_day, r_hour = item, None, None

                r_day = r_day or default_reset_day
                r_hour = r_hour or default_reset_hour
                params.append(
                    (
                        state.name,
                        state.sent_today,
                        state.sent_this_hour,
                        state.failures,
                        state.disabled_until,
                        state.last_sent,
                        r_day,
                        r_hour,
                    )
                )

            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                conn.executemany(
                    """
                    INSERT INTO smart_scheduler_state 
                    (provider_name, sent_today, sent_this_hour, failures, disabled_until, last_sent, last_reset_day, last_reset_hour)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(provider_name) DO UPDATE SET
                        sent_today=excluded.sent_today,
                        sent_this_hour=excluded.sent_this_hour,
                        failures=excluded.failures,
                        disabled_until=excluded.disabled_until,
                        last_sent=excluded.last_sent,
                        last_reset_day=excluded.last_reset_day,
                        last_reset_hour=excluded.last_reset_hour
                """,
                    params,
                )
                conn.commit()
        except Exception as e:
            logger.error(
                f"[Scheduler] Failed to save batch provider states to SQLite: {e}"
            )

    def _init_providers(self):
        self._init_db()

        # Load any existing state from SQLite
        db_states = {}
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                cursor = conn.execute(
                    "SELECT provider_name, sent_today, sent_this_hour, failures, disabled_until, last_sent, last_reset_day, last_reset_hour FROM smart_scheduler_state"
                )
                for row in cursor.fetchall():
                    db_states[row[0]] = {
                        "sent_today": row[1],
                        "sent_this_hour": row[2],
                        "failures": row[3],
                        "disabled_until": row[4],
                        "last_sent": row[5],
                        "last_reset_day": row[6],
                        "last_reset_hour": row[7],
                    }
        except Exception as e:
            logger.error(f"[Scheduler] Failed to load SQLite state: {e}")

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        hour_str = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")

        states_to_save = []

        for config in self.PROVIDER_CONFIGS:
            name = config["name"]
            state = ProviderState(
                name=name,
                daily_limit=config["daily_limit"],
                hourly_limit=config["hourly_limit"],
            )

            # If state exists in DB, load it and handle daily/hourly resets if the day/hour has changed
            if name in db_states:
                db_st = db_states[name]
                state.failures = db_st["failures"]
                state.disabled_until = db_st["disabled_until"]
                state.last_sent = db_st["last_sent"]

                state_modified = False
                # Check if daily reset is needed
                if db_st["last_reset_day"] == today_str:
                    state.sent_today = db_st["sent_today"]
                    r_day = today_str
                else:
                    state.sent_today = 0
                    r_day = today_str
                    state_modified = True

                # Check if hourly reset is needed
                if db_st["last_reset_hour"] == hour_str:
                    state.sent_this_hour = db_st["sent_this_hour"]
                    r_hour = hour_str
                else:
                    state.sent_this_hour = 0
                    r_hour = hour_str
                    state_modified = True

                if state_modified:
                    states_to_save.append((state, r_day, r_hour))
            else:
                # Insert initial row in DB
                states_to_save.append((state, today_str, hour_str))

            self.providers[name] = state

        if states_to_save:
            self._save_provider_states_to_db(states_to_save)

    def get_next_provider(self) -> Optional[str]:
        """Get next available provider with weighted rotation.
        Only considers providers with valid credentials."""
        available = []
        for name, state in self.providers.items():
            if not state.can_send():
                continue
            # Skip providers without valid credentials
            if self._active_providers and name not in self._active_providers:
                continue
            # Weight = raw remaining capacity, NOT normalized
            # Hotmail pool (25000/day) gets picked ~94% vs Gmail (100/day) ~0.4% each
            # This ensures high-capacity providers dominate the rotation naturally
            weight = max(state.remaining_today, 1)  # raw remaining count, never zero
            available.append((name, weight))

        if not available:
            return None

        total_weight = sum(w for _, w in available)
        if total_weight == 0:
            return None

        r = random.random() * total_weight
        cumulative = 0
        for name, weight in available:
            cumulative += weight
            if r <= cumulative:
                if name == self.last_provider:
                    others = [(n, w) for n, w in available if n != name]
                    if others:
                        return random.choice(others)[0]
                self.last_provider = name
                return name

        return available[-1][0]

    def calculate_delay(self) -> float:
        """Calculate delay — MAXIMUM THROUGHPUT MODE: zero delay."""
        return self.base_delay

    def should_send_now(self) -> Tuple[bool, str]:
        """Check if we should send based on Predictive Open-Rate Engine (Item 6).

        24/7 MODE: All time-based restrictions removed for continuous cloud operation.
        Weekend holds, lunch hour dead zones, and late afternoon penalties are disabled.
        """
        utc_now = datetime.now(timezone.utc)
        local_now = utc_now + timedelta(hours=self.tz_offset)
        local_hour = local_now.hour
        current_day = local_now.weekday()
        now = local_now

        # 1. Base time restrictions (using LOCAL time)
        if local_hour < self.send_start_hour:
            return False, f"Too early (before {self.send_start_hour}:00)"
        if local_hour >= self.send_end_hour:
            return False, f"Too late (after {self.send_end_hour}:00)"

        # 2. Predictive ML Dispatch Logic (Heuristic Simulation)
        # Optimal open rates are Tuesday-Thursday, 9:00 AM - 11:30 AM
        current_day = now.weekday()
        current_hour = local_hour

        # High priority dispatch window
        if current_day in (1, 2, 3) and current_hour in (9, 10, 11):
            return True, "PREDICTIVE_OPTIMAL: High Open Rate Window"

        # Weekend penalty — DISABLED for 24/7 cloud operation
        # if current_day >= 5:
        #     if random.random() < 0.8:
        #         return False, "PREDICTIVE_HOLD: Weekend - Low Open Probability"

        # Lunch hour dead zone — DISABLED for 24/7 cloud operation
        # if current_hour in (12, 13):
        #     if random.random() < 0.2:
        #         return False, "PREDICTIVE_HOLD: Lunch hour dead zone"

        # Late afternoon penalty — DISABLED for 24/7 cloud operation
        # if current_hour >= 16:
        #     if random.random() < 0.1:
        #         return False, "PREDICTIVE_HOLD: Late afternoon - likely ignored until tomorrow"

        return True, "OK"

    def record_send(self, provider: str):
        if provider in self.providers:
            self.providers[provider].record_send()
            self._save_provider_state_to_db(self.providers[provider])

    def record_failure(self, provider: str):
        if provider in self.providers:
            self.providers[provider].record_failure()
            self._save_provider_state_to_db(self.providers[provider])

    def record_success(self, provider: str):
        if provider in self.providers:
            self.providers[provider].record_success()
            self._save_provider_state_to_db(self.providers[provider])

    def get_stats(self) -> Dict:
        total_sent = sum(p.sent_today for p in self.providers.values())
        total_limit = sum(p.daily_limit for p in self.providers.values())
        available = sum(1 for p in self.providers.values() if p.can_send())

        return {
            "total_sent_today": total_sent,
            "total_daily_limit": total_limit,
            "available_providers": available,
            "total_providers": len(self.providers),
            "providers": {
                name: {
                    "sent": p.sent_today,
                    "limit": p.daily_limit,
                    "remaining": p.remaining_today,
                    "available": p.can_send(),
                    "failures": p.failures,
                }
                for name, p in self.providers.items()
            },
        }

    def reset_daily(self):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        states_to_save = []
        for provider in self.providers.values():
            provider.reset_daily()
            states_to_save.append((provider, today_str, None))
        self._save_provider_states_to_db(states_to_save)
        logger.info("Daily quotas reset")

    def reset_hourly(self):
        hour_str = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        states_to_save = []
        for provider in self.providers.values():
            provider.reset_hourly()
            states_to_save.append((provider, None, hour_str))
        self._save_provider_states_to_db(states_to_save)
        logger.info("Hourly quotas reset")

    async def wait_for_send_slot(self) -> Optional[str]:
        """Wait until we can send and return available provider.
        MAXIMUM THROUGHPUT MODE: minimal delay, instant retry.
        """
        if self._send_lock is None:
            self._send_lock = asyncio.Lock()

        async with self._send_lock:
            max_wait_cycles = 20  # More retries before giving up
            for _ in range(max_wait_cycles):
                should, reason = self.should_send_now()
                if not should:
                    await asyncio.sleep(1)  # Fast retry instead of 60s
                    continue

                provider = self.get_next_provider()
                if provider:
                    delay = self.calculate_delay()
                    await asyncio.sleep(delay)
                    return provider

                await asyncio.sleep(1)  # Fast retry instead of 60s

            logger.warning("No providers available after max wait, returning None")
            return None

    def get_warm_up_delay(self, provider: str, day_number: int) -> float:
        """Calculate warm-up delay for new provider."""
        warm_up_schedule = {
            (1, 3): 120,
            (4, 7): 90,
            (8, 14): 60,
            (15, 21): 45,
            (22, 30): 30,
        }

        for (start, end), delay in warm_up_schedule.items():
            if start <= day_number <= end:
                jitter = random.uniform(-0.2, 0.2)
                return delay * (1 + jitter)

        return self.base_delay

    def get_warm_up_volume(self, provider: str, day_number: int) -> int:
        """Get max volume for warm-up period."""
        if day_number <= 3:
            return 5
        elif day_number <= 7:
            return 10
        elif day_number <= 14:
            return 20
        elif day_number <= 21:
            return 50
        else:
            return 100


# Detect dynamic timezone offset from environment, default to Lebanon (UTC+3) for cloud deployments
try:
    _tz_offset = int(
        os.environ.get("TZ_OFFSET", os.environ.get("TIMEZONE_OFFSET", "3"))
    )
except ValueError:
    _tz_offset = 3
scheduler = SmartScheduler(tz_offset=_tz_offset)

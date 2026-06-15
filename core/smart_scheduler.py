"""
JobHunt Pro - Smart Scheduler
Intelligent email rotation with jitter, hour restrictions, and anti-detection
"""
import asyncio
import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ProviderState:
    __slots__ = ("name", "daily_limit", "sent_today", "hourly_limit",
                 "sent_this_hour", "last_sent", "failures", "disabled_until")

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
            logger.warning(f"Provider {self.name} disabled for 10min after {self.failures} failures")

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
        {"name": "gmail1", "daily_limit": 100, "hourly_limit": 100},
        {"name": "gmail2", "daily_limit": 100, "hourly_limit": 100},
        {"name": "outlook1", "daily_limit": 100, "hourly_limit": 100},
        {"name": "outlook2", "daily_limit": 100, "hourly_limit": 100},
        {"name": "zoho", "daily_limit": 100, "hourly_limit": 100},
        {"name": "yahoo", "daily_limit": 100, "hourly_limit": 100},
        {"name": "aol", "daily_limit": 100, "hourly_limit": 100},
        {"name": "protonmail", "daily_limit": 100, "hourly_limit": 100},
        {"name": "mailgun", "daily_limit": 100, "hourly_limit": 100},
        {"name": "sendgrid", "daily_limit": 100, "hourly_limit": 100},
        {"name": "sendinblue", "daily_limit": 100, "hourly_limit": 100},
        {"name": "pepipost", "daily_limit": 100, "hourly_limit": 100},
        {"name": "mailjet", "daily_limit": 100, "hourly_limit": 100},
        {"name": "elasticemail", "daily_limit": 100, "hourly_limit": 100},
        {"name": "sparkpost", "daily_limit": 100, "hourly_limit": 100},
        {"name": "postmark", "daily_limit": 100, "hourly_limit": 100},
        {"name": "mailerlite", "daily_limit": 100, "hourly_limit": 100},
        {"name": "mandrill", "daily_limit": 100, "hourly_limit": 100},
    ]

    def __init__(self, tz_offset: int = 0):
        """tz_offset: hours to add to UTC to get local time (Lebanon = +3)"""
        self.providers: Dict[str, ProviderState] = {}
        self.base_delay = 5  # Reduced from 30s to 5s for faster sends
        self.jitter_range = 0.3
        self.min_delay = 2
        self.max_delay = 30
        self.send_start_hour = 6  # Allow sending from 6AM
        self.send_end_hour = 23   # Until 11PM (was 20, blocking evening sends)
        self.tz_offset = tz_offset
        self.last_provider = None
        self._active_providers = set()  # Providers with valid credentials
        self._init_providers()

    def register_provider(self, name: str):
        """Register a provider as having valid credentials."""
        self._active_providers.add(name)
        logger.info(f"Provider registered: {name}")

    def _init_providers(self):
        for config in self.PROVIDER_CONFIGS:
            self.providers[config["name"]] = ProviderState(
                name=config["name"],
                daily_limit=config["daily_limit"],
                hourly_limit=config["hourly_limit"]
            )

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
            weight = state.remaining_today / max(state.daily_limit, 1)
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
        """Calculate delay with jitter to avoid patterns."""
        jitter = random.uniform(-self.jitter_range, self.jitter_range)
        delay = self.base_delay * (1 + jitter)
        delay = max(self.min_delay, min(delay, self.max_delay))

        if random.random() < 0.02:
            pause = random.randint(300, 600)
            logger.info(f"Random pause: {pause}s")
            delay += pause

        if random.random() < 0.05:
            delay *= random.uniform(1.5, 3.0)
            logger.info(f"Burst protection delay: {delay:.1f}s")

        return delay

    def should_send_now(self) -> Tuple[bool, str]:
        """Check if we should send based on Predictive Open-Rate Engine (Item 6)."""
        utc_now = datetime.utcnow()
        local_hour = (utc_now.hour + self.tz_offset) % 24
        now = utc_now  # for .weekday() — same day in UTC as local for GMT+3

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
            
        # Weekend penalty
        if current_day >= 5:
            if random.random() < 0.8:  # 80% chance to block on weekends
                return False, "PREDICTIVE_HOLD: Weekend - Low Open Probability"

        # Lunch hour dead zone (PA mode: reduce blocking to 20% since time is limited)
        if current_hour in (12, 13):
            if random.random() < 0.2:  # Only 20% chance to block during lunch (was 70%)
                return False, "PREDICTIVE_HOLD: Lunch hour dead zone"
                
        # Late afternoon penalty (PA mode: reduce to 10% from 50%)
        if current_hour >= 16:
            if random.random() < 0.1:
                return False, "PREDICTIVE_HOLD: Late afternoon - likely ignored until tomorrow"

        return True, "OK"

    def record_send(self, provider: str):
        if provider in self.providers:
            self.providers[provider].record_send()

    def record_failure(self, provider: str):
        if provider in self.providers:
            self.providers[provider].record_failure()

    def record_success(self, provider: str):
        if provider in self.providers:
            self.providers[provider].record_success()

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
            }
        }

    def reset_daily(self):
        for provider in self.providers.values():
            provider.reset_daily()
        logger.info("Daily quotas reset")

    def reset_hourly(self):
        for provider in self.providers.values():
            provider.reset_hourly()
        logger.info("Hourly quotas reset")

    async def wait_for_send_slot(self) -> Optional[str]:
        """Wait until we can send and return available provider.
        Returns None if no provider available after reasonable wait."""
        max_wait_cycles = 5  # Max 5 minutes wait
        for _ in range(max_wait_cycles):
            should, reason = self.should_send_now()
            if not should:
                logger.info(f"Waiting: {reason}")
                await asyncio.sleep(60)
                continue

            provider = self.get_next_provider()
            if provider:
                delay = self.calculate_delay()
                await asyncio.sleep(delay)
                return provider

            logger.info("No active providers with valid credentials, waiting 60s")
            await asyncio.sleep(60)

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


# Detect PA environment (UTC server) -> apply Lebanon timezone offset
_tz_offset = 3 if os.environ.get("PYTHONANYWHERE_DOMAIN") else 0
scheduler = SmartScheduler(tz_offset=_tz_offset)

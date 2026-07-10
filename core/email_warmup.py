"""
EMAIL WARM-UP STRATEGY
Gradually increase sending volume to avoid spam filters
Day 1: 10, Day 2: 20, Day 3: 30, Day 4: 50, Day 5+: 200
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

WARMUP_SCHEDULE = {1: 50, 2: 100, 3: 150, 4: 200, 5: 300, 6: 400, 7: 500}
WARMUP_FILE = Path("cache/email_warmup.json")
WARMUP_FILE.parent.mkdir(parents=True, exist_ok=True)


class EmailWarmup:
    """Manage email warm-up process for new accounts."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        try:
            if WARMUP_FILE.exists():
                with open(WARMUP_FILE) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Warmup load failed: {e}")
        return {"providers": {}}

    def _save(self):
        try:
            with open(WARMUP_FILE, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.warning(f"Warmup save failed: {e}")

    def _get_day_number(self, provider: str) -> int:
        """Get which warmup day we're on for this provider."""
        p = self.data["providers"].get(provider, {})
        first_send = p.get("first_send_date")
        if not first_send:
            return 0
        first = datetime.fromisoformat(first_send)
        return (datetime.now() - first).days + 1

    def get_daily_limit(self, provider: str) -> int:
        """Get max emails allowed today for this provider."""
        day = self._get_day_number(provider)
        if day == 0:
            return WARMUP_SCHEDULE[1]  # Not started yet, use day 1 limit
        # Clamp to max schedule day (7) which has limit 500
        return WARMUP_SCHEDULE.get(min(day, max(WARMUP_SCHEDULE.keys())), 500)

    def get_sent_today(self, provider: str) -> int:
        """Get number of emails sent today."""
        p = self.data["providers"].get(provider, {})
        today = datetime.now().strftime("%Y-%m-%d")
        if p.get("last_send_date") == today:
            return p.get("sent_today", 0)
        return 0

    def can_send(self, provider: str) -> bool:
        """Check if we can send more emails today."""
        return self.get_sent_today(provider) < self.get_daily_limit(provider)

    def record_send(self, provider: str, count: int = 1):
        """Record that we sent emails."""
        today = datetime.now().strftime("%Y-%m-%d")
        if provider not in self.data["providers"]:
            self.data["providers"][provider] = {
                "first_send_date": datetime.now().isoformat(),
                "last_send_date": today,
                "sent_today": 0,
                "total_sent": 0,
            }

        p = self.data["providers"][provider]
        if p.get("last_send_date") != today:
            p["sent_today"] = 0
            p["last_send_date"] = today

        p["sent_today"] = p.get("sent_today", 0) + count
        p["total_sent"] = p.get("total_sent", 0) + count
        self._save()

    def get_status(self, provider: str) -> dict:
        """Get warmup status for a provider."""
        day = self._get_day_number(provider)
        limit = self.get_daily_limit(provider)
        sent = self.get_sent_today(provider)
        return {
            "provider": provider,
            "warmup_day": day,
            "daily_limit": limit,
            "sent_today": sent,
            "remaining": max(0, limit - sent),
            "is_warmed_up": day >= 7,
        }


# Global instance
warmup = EmailWarmup()

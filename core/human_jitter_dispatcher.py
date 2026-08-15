"""
core/human_jitter_dispatcher.py - Gaussian Human Jitter Dispatch Engine
JobHunt Pro SaaS - Modulates email send pacing with natural normal/Gaussian distribution,
effectively evading automated ESP rate-trap filters and spam triggers.
"""

import random
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("human_jitter")

class HumanJitterDispatcher:
    """
    Simulates human pacing behavior for automated dispatches.
    Standard mean: 120 seconds, standard deviation: 35 seconds, clamped between min_delay and max_delay.
    """

    def __init__(
        self,
        mean_delay: float = 120.0,
        std_deviation: float = 35.0,
        min_delay: float = 45.0,
        max_delay: float = 240.0
    ):
        self.mean_delay = mean_delay
        self.std_deviation = std_deviation
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.history = []

    def compute_next_delay(self) -> float:
        """Calculates randomized delay (seconds) following a Gaussian curve."""
        delay = random.gauss(self.mean_delay, self.std_deviation)
        clamped_delay = max(self.min_delay, min(self.max_delay, delay))
        # Add slight micro-jitter (0.1 to 1.5 seconds)
        micro_jitter = random.uniform(0.1, 1.5)
        final_delay = round(clamped_delay + micro_jitter, 2)
        
        self.history.append(final_delay)
        if len(self.history) > 100:
            self.history.pop(0)
            
        return final_delay

    async def wait_jitter(self, custom_multiplier: float = 1.0) -> float:
        """Asynchronously waits for the computed jitter delay."""
        delay = self.compute_next_delay() * max(0.1, custom_multiplier)
        logger.info(f"⏳ Human Jitter Pacing: Sleeping for {delay:.1f}s before next dispatch...")
        await asyncio.sleep(delay)
        return delay

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns statistical telemetry on recent delays."""
        if not self.history:
            return {"average_delay": self.mean_delay, "total_delays": 0}
        return {
            "average_delay": round(sum(self.history) / len(self.history), 2),
            "min_recorded": min(self.history),
            "max_recorded": max(self.history),
            "total_delays": len(self.history)
        }

# Global singleton
human_jitter = HumanJitterDispatcher()

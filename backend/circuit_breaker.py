"""
Resilient External API Circuit Breaker & Fallback Guard for JobHunt Pro SaaS.
Protects the platform from cascading external API failures (LLMs, DNS resolvers, MX checks).
"""

import time
import logging
from typing import Callable, Any, Optional, Dict

logger = logging.getLogger(__name__)


class CircuitBreakerOpenException(Exception):
    """Raised when an execution call is attempted while the circuit is OPEN."""
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self.failure_count = 0
        self.success_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_state_change = time.time()
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.last_state_change = now
                logger.info(f"CircuitBreaker '{self.name}' transitioned from OPEN to HALF_OPEN")
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        if self.state in ("HALF_OPEN", "OPEN"):
            self.state = "CLOSED"
            self.last_state_change = time.time()
            logger.info(f"CircuitBreaker '{self.name}' reset to CLOSED")

    def record_failure(self, exc: Exception):
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"CircuitBreaker '{self.name}' failure count: {self.failure_count}/{self.failure_threshold} ({exc})")

        if self.failure_count >= self.failure_threshold or self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.last_state_change = time.time()
            logger.error(f"CircuitBreaker '{self.name}' TRIPPED to OPEN state")

    async def call_async(self, func: Callable, *args, fallback: Optional[Callable] = None, **kwargs) -> Any:
        if not self.can_execute():
            if fallback:
                logger.info(f"CircuitBreaker '{self.name}' OPEN. Executing fallback.")
                return fallback(*args, **kwargs) if not callable(fallback) else fallback()
            raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN. Requests blocked.")

        try:
            res = await func(*args, **kwargs)
            self.record_success()
            return res
        except self.expected_exceptions as e:
            self.record_failure(e)
            if fallback:
                return fallback() if callable(fallback) else fallback
            raise e

    def call_sync(self, func: Callable, *args, fallback: Optional[Callable] = None, **kwargs) -> Any:
        if not self.can_execute():
            if fallback:
                logger.info(f"CircuitBreaker '{self.name}' OPEN. Executing sync fallback.")
                return fallback() if callable(fallback) else fallback
            raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN. Requests blocked.")

        try:
            res = func(*args, **kwargs)
            self.record_success()
            return res
        except self.expected_exceptions as e:
            self.record_failure(e)
            if fallback:
                return fallback() if callable(fallback) else fallback
            raise e

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout,
            "last_state_change_seconds_ago": round(time.time() - self.last_state_change, 2)
        }


# Default global circuit breakers for key external services
global_mx_circuit_breaker = CircuitBreaker("MX_Shield_DNS", failure_threshold=3, recovery_timeout=15.0)
global_ai_circuit_breaker = CircuitBreaker("AI_SDR_LLM", failure_threshold=5, recovery_timeout=20.0)

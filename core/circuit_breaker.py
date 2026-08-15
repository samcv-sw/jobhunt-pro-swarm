"""
core/circuit_breaker.py - Enterprise Resilience & Circuit Breaker Engine
JobHunt Pro SaaS - Prevents systemic cascading failures & handles API retries with jittered exponential backoff.
"""

import asyncio
import inspect
import logging
import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type, Any, Dict

logger = logging.getLogger(__name__)


class CircuitBreakerOpenException(Exception):
    """Raised when a circuit breaker is in OPEN state and blocks requests."""
    pass


class CircuitBreaker:
    """
    Enterprise Circuit Breaker implementation for both synchronous and asynchronous functions.
    Prevents cascading failures when external services, LLM providers, or mail gateways face outages.
    """
    def __init__(self, max_failures: int = 5, reset_timeout: int = 60, name: str = "default") -> None:
        self.name = name
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.success_count = 0
        self.trip_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_error_message: Optional[str] = None
        self.state = 'CLOSED'  # States: CLOSED, OPEN, HALF_OPEN

    def _record_failure(self, error: Optional[Exception] = None) -> None:
        """Increment failure count and open the circuit if threshold is reached."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if error:
            self.last_error_message = str(error)
        if self.failure_count >= self.max_failures:
            if self.state != 'OPEN':
                self.trip_count += 1
            self.state = 'OPEN'
            logger.warning(
                f"[CircuitBreaker:{self.name}] TRIPPED to OPEN! (Failures: {self.failure_count}/{self.max_failures}, Last error: {self.last_error_message})"
            )

    def _record_success(self) -> None:
        """Reset failure count and close the circuit on successful call."""
        self.failure_count = 0
        self.success_count += 1
        self.state = 'CLOSED'
        self.last_error_message = None

    def reset(self) -> None:
        """Manually reset the circuit breaker back to CLOSED state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.last_error_message = None
        self.state = 'CLOSED'

    def get_metrics(self) -> Dict[str, Any]:
        """Returns runtime diagnostic metrics for monitoring dashboards."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "trip_count": self.trip_count,
            "max_failures": self.max_failures,
            "reset_timeout": self.reset_timeout,
            "last_failure_time": self.last_failure_time,
            "last_error_message": self.last_error_message
        }

    def __call__(self, func: Callable) -> Callable:
        """Wrap a sync or async function with circuit breaker logic."""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self.last_failure_time and (time.time() - self.last_failure_time > self.reset_timeout):
                    self.state = 'HALF_OPEN'
                    logger.info(f"[CircuitBreaker:{self.name}] State: HALF_OPEN. Testing canary request...")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit Breaker '{self.name}' is OPEN. Request blocked to prevent systemic failure."
                    )

            try:
                result = await func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    logger.info(f"[CircuitBreaker:{self.name}] Canary succeeded. State returned to CLOSED.")
                    self._record_success()
                else:
                    self.success_count += 1
                return result
            except Exception as e:
                if not isinstance(e, CircuitBreakerOpenException):
                    self._record_failure(e)
                raise e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self.last_failure_time and (time.time() - self.last_failure_time > self.reset_timeout):
                    self.state = 'HALF_OPEN'
                    logger.info(f"[CircuitBreaker:{self.name}] State: HALF_OPEN. Testing canary request...")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit Breaker '{self.name}' is OPEN. Request blocked to prevent systemic failure."
                    )

            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    logger.info(f"[CircuitBreaker:{self.name}] Canary succeeded. State returned to CLOSED.")
                    self._record_success()
                else:
                    self.success_count += 1
                return result
            except Exception as e:
                if not isinstance(e, CircuitBreakerOpenException):
                    self._record_failure(e)
                raise e

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
    fallback_value: Any = None,
    use_fallback: bool = False
) -> Callable:
    """
    Decorator for robust retry logic with exponential backoff and randomized full jitter.
    Supports both synchronous and asynchronous functions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_retry_wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    if circuit_breaker:
                        return await circuit_breaker(func)(*args, **kwargs)
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if isinstance(exc, CircuitBreakerOpenException):
                        if use_fallback:
                            logger.warning(f"[RetryBackoff] Circuit breaker open for {func.__name__}. Using fallback.")
                            return fallback_value
                        raise exc
                    
                    if attempt == max_retries:
                        logger.error(
                            f"[RetryBackoff] Max retries ({max_retries}) reached for {func.__name__}: {exc}"
                        )
                        if use_fallback:
                            return fallback_value
                        raise exc
                    
                    sleep_time = min(max_delay, delay * (backoff_factor ** (attempt - 1)))
                    if jitter:
                        sleep_time = random.uniform(0.5 * sleep_time, sleep_time)
                    logger.info(
                        f"[RetryBackoff] Attempt {attempt}/{max_retries} failed for {func.__name__} ({exc}). Retrying in {sleep_time:.2f}s..."
                    )
                    await asyncio.sleep(sleep_time)
            if use_fallback:
                return fallback_value
            if last_exc:
                raise last_exc

        @wraps(func)
        def sync_retry_wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    if circuit_breaker:
                        return circuit_breaker(func)(*args, **kwargs)
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if isinstance(exc, CircuitBreakerOpenException):
                        if use_fallback:
                            logger.warning(f"[RetryBackoff] Circuit breaker open for {func.__name__}. Using fallback.")
                            return fallback_value
                        raise exc
                    
                    if attempt == max_retries:
                        logger.error(
                            f"[RetryBackoff] Max retries ({max_retries}) reached for {func.__name__}: {exc}"
                        )
                        if use_fallback:
                            return fallback_value
                        raise exc
                    
                    sleep_time = min(max_delay, delay * (backoff_factor ** (attempt - 1)))
                    if jitter:
                        sleep_time = random.uniform(0.5 * sleep_time, sleep_time)
                    logger.info(
                        f"[RetryBackoff] Attempt {attempt}/{max_retries} failed for {func.__name__} ({exc}). Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
            if use_fallback:
                return fallback_value
            if last_exc:
                raise last_exc

        if inspect.iscoroutinefunction(func):
            return async_retry_wrapper
        return sync_retry_wrapper
    return decorator


# Pre-configured instances for production critical services
email_circuit_breaker = CircuitBreaker(max_failures=3, reset_timeout=120, name="email_smtp_gateway")
scraper_circuit_breaker = CircuitBreaker(max_failures=5, reset_timeout=300, name="web_scraper_swarm")
llm_circuit_breaker = CircuitBreaker(max_failures=4, reset_timeout=60, name="ai_llm_orchestrator")

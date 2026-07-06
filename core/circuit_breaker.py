import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    """
    A lightweight Circuit Breaker implementation for async functions.
    Prevents cascading failures when external services go down.
    """
    def __init__(self, max_failures=5, reset_timeout=60):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # States: CLOSED, OPEN, HALF_OPEN

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.state = 'OPEN'
            logger.warning(f"Circuit Breaker TRIPPED! State: OPEN. (Failures: {self.failure_count})")

    def _record_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'

    def __call__(self, func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit Breaker state: HALF_OPEN. Testing external service...")
                else:
                    raise CircuitBreakerOpenException("Circuit Breaker is OPEN. Request blocked to prevent systemic failure.")

            try:
                result = await func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    logger.info("Circuit Breaker test succeeded. State: CLOSED.")
                    self._record_success()
                return result
            except Exception as e:
                # We do not catch CircuitBreakerOpenException here, let it propagate
                if not isinstance(e, CircuitBreakerOpenException):
                    self._record_failure()
                raise e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit Breaker state: HALF_OPEN. Testing external service...")
                else:
                    raise CircuitBreakerOpenException("Circuit Breaker is OPEN. Request blocked to prevent systemic failure.")

            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    logger.info("Circuit Breaker test succeeded. State: CLOSED.")
                    self._record_success()
                return result
            except Exception as e:
                if not isinstance(e, CircuitBreakerOpenException):
                    self._record_failure()
                raise e
                
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

# Pre-configured instances for common failure points
email_circuit_breaker = CircuitBreaker(max_failures=3, reset_timeout=120)
scraper_circuit_breaker = CircuitBreaker(max_failures=5, reset_timeout=300)
llm_circuit_breaker = CircuitBreaker(max_failures=4, reset_timeout=60)

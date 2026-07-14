# Handoff Report: Groq LLM Rate-Limit Controller & Free Fallbacks

This report documents the implementation of the Groq LLM Rate-Limit Controller and fallback mechanisms for Milestone 3, as well as verification results.

---

## 1. Observation

- **Core Provider Pool (`core/llm_provider_pool.py`)**: 
  - Originally returned `None` and added simulated local delays when encountering HTTP 429 rate limit statuses (lines 368-376). It did not raise exceptions or share rate-limit status globally via the Redis-based `edge_cache`.
- **Inference calls (`backend/ai_engine.py`)**: 
  - Called `llm_pool.complete()` without specifying `preferred_provider=LLMProvider.GROQ` (lines 65 and 143), hindering routing optimization for the Llama-3 (LPU) task.
- **Celery Tasks (`backend/tasks.py`)**: 
  - Had a simple try-except block wrapping `generate_cover_letter` (lines 55-68) that unconditionally retried task failures with a hardcoded `countdown=10`, failing to check the cache or adapt countdown values based on actual rate limit reset headers.
- **Test Suite (`tests/test_llm_provider_pool.py`)**: 
  - Had 5 basic tests covering daily limit checks and fallback routing, but lacked coverage for header parsing, decorator-based retries, or rate limit exception propagation.

---

## 2. Logic Chain

1. **Routing Optimization**:
   - Specified `preferred_provider=LLMProvider.GROQ` in the `backend/ai_engine.py` calls to ensure the pool prioritizes Groq LPU models as intended.
2. **Robust Rate-Limit Exception (`LLMRateLimitError`)**:
   - Introduced a subclass of `Exception` that contains `reset_time` and `provider` properties to easily communicate HTTP 429 conditions from individual provider instances to the pool and ultimately the worker.
3. **Response Header Extraction**:
   - Added parsing logic (`parse_groq_reset_time`) to convert Groq's custom string duration format (e.g. `1.2s`, `15ms`, `6m15s`) to float seconds.
   - When a Groq request succeeds but leaves remaining requests at `0` (headers indicate exhausted capacity), or when it fails with HTTP `429`, the reset time is parsed and the absolute epoch timestamp (`time.time() + reset_time`) is saved in the global `edge_cache` under `"groq_rate_limit_reset"`.
4. **Resilient Fallback Rotation**:
   - In `ProviderInstance.complete`, a specific `except LLMRateLimitError: raise` block is registered to prevent the generic `except Exception` from catching and swallowing the custom rate-limit exception.
   - In `LLMProviderPool.complete`, caught rate-limit errors from the candidate loop are saved (`last_rate_limit_err`). The pool continues to rotate through other free-tier candidates (e.g. Gemini, Cerebras). If all candidates fail and the last encountered issue was a rate limit, the `LLMRateLimitError` is raised.
5. **Smart Celery retries (`@groq_rate_limit_retry`)**:
   - **Proactive**: Checks the global cache key `"groq_rate_limit_reset"` prior to running. If active and in the future, the task is proactively retried with the exact duration + 1s buffer.
   - **Reactive**: Catches `LLMRateLimitError` during execution and schedules a retry with `countdown = reset_time + 1`.

---

## 3. Caveats

- **Active Event Loops in Tests**:
  - The Celery decorator retry logic relies on executing a synchronous wrapper function, which uses the internal `run_async` helper (which calls `asyncio.run_coroutine_threadsafe(...).result()`). When running tests using `pytest-asyncio`, the thread already has a running event loop. Invoking `.result()` blocks the thread and deadlocks the loop. To prevent this, the unit test (`test_groq_rate_limit_retry_decorator`) was kept synchronous (without `async def` or `@pytest.mark.asyncio`), forcing `run_async` to run inside a clean standalone event loop.
- **Revive Checks during Fallback Tests**:
  - In fallback tests, setting the other provider flags to unhealthy triggers the pool's post-loop health revive check `await pool._health_check()`. This loop makes sequential network calls to revive other providers, causing major timeouts. We explicitly mock `pool._health_check = AsyncMock()` in `test_pool_fallback_and_exception_propagation` to isolate LLM pool fallback routing and ensure test speed.

---

## 4. Conclusion

The Groq Rate-Limit Controller & Free Fallbacks have been successfully implemented across all targeted files:
- `core/llm_provider_pool.py`: Fully parses Groq's reset headers, caches values globally, and propagates `LLMRateLimitError`.
- `backend/ai_engine.py`: Routes cover letter generation to Groq as the preferred provider.
- `backend/tasks.py`: Added decorator-based retry policy for cover letter generation.
- `tests/test_llm_provider_pool.py`: Enhanced test suite with 4 new unit tests. All 9 tests passed.

---

## 5. Verification Method

### Execution Command
Verify the implementation using pytest:
```powershell
pytest tests/test_llm_provider_pool.py
```

### Verification Verification Output
```
collected 9 items

tests\test_llm_provider_pool.py .........                                [100%]

============================== 9 passed in 8.63s ==============================
```

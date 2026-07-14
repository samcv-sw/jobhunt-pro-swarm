# Milestone 3 Explorer Handoff: Groq LLM Rate-Limit Controller & Free Fallbacks

This report outlines the implementation strategy for adding a Celery rate-limiting retrier and a free-tier LLM fallback mechanism when hitting Groq API rate limits (HTTP 429).

---

## 1. Observation

During our exploration of the codebase, the following files and components were analyzed:

| File Path | Description / Key Observations |
|---|---|
| `backend/tasks.py` | Defines Celery tasks. `generate_cover_letter` (lines 55-68) is a synchronous wrapper around the async `generate_smart_cover_letter` function. It retries on *any* exception with a hardcoded `countdown=10` seconds (lines 65-67). |
| `backend/ai_engine.py` | Contains `generate_smart_cover_letter` (lines 23-93) and `generate_smart_cover_letter_stream` (lines 94-174), both invoking `llm_pool.complete` (lines 65-70 and 143-148) without specifying a preferred provider. |
| `core/llm_provider_pool.py` | Manages 17 free LLM providers, including Groq (lines 68-83). The `ProviderInstance.complete` method (lines 301-414) intercepts HTTP `429` errors (lines 368-376) but silences them, returning `None` and attempting to simulate rate limit state locally in `_request_times` rather than propagating the reset duration or caching it globally. |
| `core/edge_cache.py` | Implements an Upstash Redis REST-based global cache singleton `edge_cache` (lines 8-76), which can be leveraged to share rate limit state dynamically across multiple parallel Celery worker processes. |

### Relevant Code Details

#### Verbatim excerpt from `backend/tasks.py` (lines 55-68):
```python
@celery_app.task(bind=True, max_retries=3)
def generate_cover_letter(self, job_description: str, user_cv: str):
    """
    Background task to generate cover letter via Groq Llama 3 (LPU).
    """
    logger.info("Generating cover letter using Groq LPU...")
    try:
        # Run the async AI generation within the synchronous Celery worker
        result = run_async(generate_smart_cover_letter(job_description, user_cv))
        return {"status": "success", "subject": result.get("subject"), "body": result.get("body")}
    except Exception as exc:
        logger.error(f"AI Generation failed: {exc}")
        raise self.retry(exc=exc, countdown=10)
```

#### Verbatim excerpt from `core/llm_provider_pool.py` (lines 368-376):
```python
            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 5))
                logger.warning(
                    f"Provider {self.config.name.value} 429, rate limited. Switching keys on next request if available."
                )
                # Temporarily add fake requests to trigger the rate limit wait logic for next calls
                for _ in range(self.config.rate_limit_rpm):
                    self._request_times.append(time.time() + retry_after)
                return None
```

---

## 2. Logic Chain

1. **Preferred Provider Routing**: 
   Since `generate_cover_letter` in `backend/tasks.py` specifically states it generates the letter "via Groq Llama 3 (LPU)", the underlying calls in `backend/ai_engine.py` should explicitly prioritize Groq using the `preferred_provider=LLMProvider.GROQ` parameter inside `llm_pool.complete`.
   
2. **Rate Limit Extraction**: 
   When Groq's API is invoked, it returns rate-limit metrics in its HTTP headers:
   - `x-ratelimit-remaining` (indicates remaining requests inside the window)
   - `x-ratelimit-reset` (indicates the time remaining, e.g., `"1.2s"`, `"15ms"`, `"6m15s"` until the limit resets).
   We must parse these headers on every response (success and 429).
   
3. **Global Rate Limit Sharing**: 
   Because Celery workers run in separate processes (and potentially different nodes), process-local tracking is insufficient. We should store the absolute reset epoch timestamp (`time.time() + reset_time`) in the shared `edge_cache` Redis under the key `"groq_rate_limit_reset"` with a TTL equal to the reset time. This informs all Celery workers of active rate-limits.
   
4. **Proactive & Reactive Delays in Celery**:
   - **Proactive**: Before running `generate_cover_letter`, a custom task decorator `groq_rate_limit_retry` checks `edge_cache` for `"groq_rate_limit_reset"`. If present and in the future, the task is immediately retried via `self.retry(countdown=...)` without making a redundant API call.
   - **Reactive**: If a 429 occurs, a custom exception `LLMRateLimitError` is raised from the provider instance, carrying the `reset_time` (parsed from `x-ratelimit-reset` or `retry-after`).
   
5. **Fallback Flow in Pool**:
   In `core/llm_provider_pool.py`, if Groq triggers an `LLMRateLimitError`, the pool catches it, logs it, and continues the candidates loop to try fallback providers (e.g. Gemini, Cerebras, HuggingFace). If a fallback succeeds, the task succeeds without interruption. If all fallback options are exhausted, the pool propagates the `LLMRateLimitError` back up, allowing the Celery decorator to catch it and trigger a task retry.

---

## 3. Caveats

- **Upstash Redis REST API Performance**: Checking `edge_cache` before every task run adds a lightweight HTTP request. If Upstash latency is high, this may delay task initialization by ~50-100ms.
- **Dynamic API Key Rotation**: Groq supports rotating multiple keys defined in `GROQ_API_KEY`. If one key is rate-limited, others might still be active. Proactively blocking *all* tasks when one key hits 429 assumes that all keys are exhausted. However, since the rotation is random, key exhaustion is typically correlated, making proactive blocking a safe default to prevent repeated 429s.
- **RTL and UI Layout**: No UI modifications are needed for this backend rate-limit controller.

---

## 4. Conclusion

We recommend applying the changes captured in `groq_rate_limit.patch` to implement a multi-layered rate limit handler:
1. **Header Parsing Utility**: Adds a parser for Groq's time string format (supporting `h`, `m`, `s`, `ms` units).
2. **State Sharing**: Caches active rate limit reset times in `edge_cache` when remaining capacity reaches `0` or on `429`.
3. **Proactive Task Delay**: Uses a custom `@groq_rate_limit_retry` decorator to inspect the cache and dynamically postpone Celery tasks using `self.retry()`.
4. **Resilient Failover**: Maintains the pool's automatic provider rotation and propagates the rate limit exception only when all providers fail.

The precise modifications are formatted as a unified git diff in `.agents/explorer_m3_groqlimit/groq_rate_limit.patch`.

---

## 5. Verification Method

### Test Cases to Implement:

1. **Parser Tests (`tests/test_llm_provider_pool.py`)**:
   Verify that `parse_groq_reset_time` handles all of Groq's reset formats:
   ```python
   def test_parse_groq_reset_time():
       assert parse_groq_reset_time("1.2s") == 1.2
       assert parse_groq_reset_time("15ms") == 0.015
       assert parse_groq_reset_time("72ms") == 0.072
       assert parse_groq_reset_time("6m15s") == 375.0
       assert parse_groq_reset_time("1h2m3s") == 3723.0
       assert parse_groq_reset_time("") == 0.0
   ```

2. **Celery Decorator Mock Tests**:
   Mock the `edge_cache` GET response with a future timestamp and confirm that the wrapped Celery task raises a `celery.exceptions.Retry` with the correct `countdown`.

3. **Pool Fallback and Exception Propagation Test**:
   Mock Groq to return `429` with header `x-ratelimit-reset: 10s`. Mock all other providers to fail. Ensure `llm_pool.complete()` raises `LLMRateLimitError` with `reset_time=10.0` and `provider="groq"`.

### Run Test Command:
Execute the test suite using `pytest`:
```bash
pytest tests/test_llm_provider_pool.py
```

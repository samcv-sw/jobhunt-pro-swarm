# Handoff Report: Milestone 5 (AI Model Upgrades)

## 1. Observation

- **LLM Provider Pool Entry Point**: The core multi-provider LLM rotation and fallback logic is located in `core/llm_provider_pool.py`.
- **Existing Gemini Configuration**: In `core/llm_provider_pool.py`, Gemini is configured as:
  ```python
  # ═══ GEMINI (free) ═══
  ProviderConfig(
      name=LLMProvider.GEMINI,
      api_key_env="GEMINI_API_KEY",
      base_url="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
      models=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"],
      rate_limit_rpm=60,
      weight=10,
      daily_limit=1500,
  ),
  ```
  `gemini-1.5-pro` is already the primary (first listed) model for the Gemini provider.
- **Client Implementation**: `ProviderInstance` initializes an async HTTP client (line 321):
  ```python
  self._client = httpx.AsyncClient(timeout=60.0)
  ```
  And makes raw POST requests. For example, for Gemini (lines 382–396):
  ```python
  if self.config.name == LLMProvider.GEMINI:
      url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
      payload = {
          "contents": [
              {
                  "role": "user",
                  "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
              }
          ],
          "generationConfig": {
              "temperature": temperature,
              "maxOutputTokens": max_tokens,
          },
      }
      headers = {"Content-Type": "application/json"}
  ```
- **Consumer Modules**: 
  - **Cover Letter Generation**: Located in `core/ai_tailor.py`. It integrates with `LLMProviderPool` via `self.llm_pool.complete(...)` in the `_call_ai(...)` method (lines 896–903):
    ```python
    if self.llm_pool:
        try:
            result = await self.llm_pool.complete(
                system_prompt="You are a professional career advisor...",
                user_prompt=current_prompt,
                ...
            )
    ```
  - **Resume ATS Matching**: Located in `core/ats_matcher.py`. It integrates via `pool.complete(...)` in `analyze_with_groq_async(...)` (lines 1198–1203):
    ```python
    pool = _get_llm_pool()
    if pool:
        try:
            content = await pool.complete(
                system_prompt="You are an ATS expert. Answer in JSON only.",
                user_prompt=prompt,
                ...
            )
    ```

---

## 2. Logic Chain

1. Since both Cover Letter generation (`core/ai_tailor.py`) and Resume ATS matching (`core/ats_matcher.py`) consume the LLM pool dynamically via the `LLMProviderPool.complete(...)` abstraction, modifying `core/llm_provider_pool.py` is the only change required to add new models, fallback routes, or rotation strategies globally.
2. `gemini-1.5-pro` is already integrated as the default model under `LLMProvider.GEMINI`.
3. Claude 3.5 Sonnet is currently completely absent from the provider pool (no enum value, config, or HTTP formatting/parsing rules).
4. Since the provider pool is built entirely around direct async REST API calls via `httpx.AsyncClient` rather than utilizing provider-specific client libraries, Claude 3.5 Sonnet should be added via raw HTTP POSTs to the Anthropic Messages API. This maintains the zero-cost/dependency-free architecture.
5. In addition to adding the provider configurations, the environment variable `ANTHROPIC_API_KEY` must be loaded, and the pool test environment must be updated to clean this variable when running tests.

---

## 3. Caveats

- **Free Tier Rate Limits**: Anthropic's free tier has a low rate limit (e.g., 5 RPM). In a production or high-throughput environment, this limit should be adjusted.
- **API Payload Assumptions**: The proposed payload structure assumes Anthropic Messages API version `2023-06-01`. Any future deprecation or breaking changes to this endpoint would invalidate this implementation.

---

## 4. Conclusion

### Required Environment Variables
- `GEMINI_API_KEY`: API key for Google Gemini Developer API.
- `ANTHROPIC_API_KEY`: API key for Anthropic Claude API.

### Required API Client Libraries
- **None**: Direct REST calls via the existing `httpx` package are recommended, keeping the implementation lightweight.
- *(Optional SDKs if refactoring client instantiation: `google-generativeai` and `anthropic`)*

### Proposed Code Changes (for Implementer)

#### A. Edit `core/llm_provider_pool.py`

1. **Add `ANTHROPIC` to `LLMProvider` Enum**:
   ```python
   class LLMProvider(Enum):
       ...
       QWEN = "qwen"
       ANTHROPIC = "anthropic"
       DUMMY = "dummy"
   ```

2. **Add Claude 3.5 Sonnet to `PROVIDER_CONFIGS`**:
   ```python
   PROVIDER_CONFIGS = [
       ...
       # ═══ ANTHROPIC (Claude 3.5 Sonnet) ═══
       ProviderConfig(
           name=LLMProvider.ANTHROPIC,
           api_key_env="ANTHROPIC_API_KEY",
           base_url="https://api.anthropic.com/v1/messages",
           models=["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-latest"],
           rate_limit_rpm=5,
           weight=9, # High weight for high-quality generation
           daily_limit=0,
       ),
       ...
   ]
   ```

3. **In `ProviderInstance.complete()`, handle Anthropic request headers and payload**:
   ```python
           # (Under payload construction section, around line 397)
           elif self.config.name == LLMProvider.ANTHROPIC:
               headers = {
                   "x-api-key": api_key,
                   "anthropic-version": "2023-06-01",
                   "content-type": "application/json",
               }
               payload = {
                   "model": model,
                   "messages": [
                       {"role": "user", "content": user_prompt}
                   ],
                   "system": system_prompt,
                   "max_tokens": max_tokens,
                   "temperature": temperature,
               }
   ```

4. **In `ProviderInstance.complete()`, handle Anthropic response parsing**:
   ```python
               # (Under response parsing section, around line 487)
               elif self.config.name == LLMProvider.ANTHROPIC:
                   data = response.json()
                   content = data.get("content", [])
                   if content and content[0].get("type") == "text":
                       return content[0].get("text", "")
                   return None
   ```

---

## 5. Verification Method

- Run the pytest suite on the LLM pool to verify no regressions:
  ```bash
  test_env\Scripts\pytest tests/test_llm_provider_pool.py
  ```
- **Falsification/Invalidation condition**: The implementation is considered invalid if an `ANTHROPIC_API_KEY` is provided in `.env`, but requests to Claude fail with `HTTP 400 (Bad Request)` due to incorrect payload format, or if `tests/test_llm_provider_pool.py` fails to run successfully due to code injection errors in `core/llm_provider_pool.py`.

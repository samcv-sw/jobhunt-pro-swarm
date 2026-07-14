## 2026-07-10T20:48:56Z
You are the primary implementer worker. Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_cloud_optimize.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your objectives:
1. Diagnose and fix the RuntimeWarning (concerning unawaited mock coroutines) in tests/test_stealth_parser_and_fallbacks.py. First, run the test and check the exact warnings.
2. Implement Single-Container Web+Worker Fusion:
   - Edit start_cloud.py to run Celery with solo pool (-P solo -c 1) to save memory.
   - Edit backend/celery_app.py to fall back to REDIS_URL if RABBITMQ_URL is not set.
   - Edit backend/database.py to scale down pool_size to 3 and max_overflow to 2 in PostgreSQL pool configuration, and set PRAGMA cache_size=-2000 in SQLite to reduce memory usage under 512MB RAM.
3. Implement Edge-Cached Semantic Engine & Failover Pool:
   - Update backend/ai_engine.py to use the multi-provider LLM pool (LLMProviderPool) and integrate EdgeCache (REST API client) from core/edge_cache.py to cache cover letter generations using a hash key (e.g. SHA-256 of user_cv + job_description).
   - Ensure cached responses return in < 100ms.
   - Integrate edge caching in core/ats_matcher.py for ATS matching/scoring using the same Upstash Redis client.
4. Upgrade Stealth Scraping & TLS Fingerprinting:
   - Edit core/stealth.py to map newer unsupported browser profiles (chrome131, chrome130, chrome129, safari18_0, edge99) to supported curl_cffi strings (chrome120, safari17_2_1).
   - Inject the robust Canvas spoofing script (pixel-by-pixel noise) inside NodriverFallback (in core/stealth.py) rather than the basic script.
   - Enhance core/stealth_http.py to support Chrome TLS JA3 fingerprinting and session reuse across multiple requests.
5. Implement SMTP Warmup & Telegram Webhook:
   - Integrate core/email_warmup.py into core/email_engine.py so that SMTP warmup schedule and ramp-up is enforced.
   - Add a Celery/background warmup task/loop in core/free_smtp_pool.py to preserve sender reputation.
   - Migrate Telegram bot from long-polling to webhook hosted in backend/main.py. Register POST /webhook/telegram endpoint in backend/main.py and call setWebhook on startup (lifespan) using the bot token.

When done, run the full test suite (pytest) and verify everything passes (100% success rate, no warnings, no failures). Write your handoff report changes.md in your working directory.

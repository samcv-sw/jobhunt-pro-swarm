## 2026-07-12T13:59:35Z
You are Worker M3. Your working directory is C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m3_shield.
Your task is to implement Milestone 3: DB and Cache Rate-Limit Shield.
Specifically:
1. Add a thread-safe L1 memory cache shield inside core/edge_cache.py as an in-process cache wrapper in front of Redis L2 REST API calls, mapping TTL by key prefix (immutable cover letters for 10 min, ATS score for 30 min, campaigns for 1 min, rate-limit resets for 5 sec).
2. Change the ASGI rate limiter in web/app_v2.py (SecureCORSMiddleware / RateLimitingMiddleware) to run purely in memory using a thread-safe sliding window to save 100% of Upstash Redis rate-limit calls.
3. Update core/ats_matcher.py (and any other files calling synchronous standard redis) to use the async edge_cache client (with L1 memory cache shield) asynchronously.
4. Harden direct asyncpg connection pool parameters in core/async_db.py to match SQLAlchemy limits (max_size=3), route to the -pooler endpoint, disable prepared statement caching (statement_cache_size=0), and set a 280s idle connection lifetime.
5. Implement the SQLite Write-Buffer / Failover Query Queue (pending_query_queue) in core/pg_sqlite_shim.py to buffer writes when Neon PostgreSQL is offline or waking up, and process them asynchronously in a background loop.
Refer to C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_1\handoff.md and C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2\handoff.md for design patterns.

MANDATORY INTEGRITY WARNING — DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Run tests using 'pytest' to verify no regressions and that the caching layers function as expected. Document changes and test logs in your handoff report.

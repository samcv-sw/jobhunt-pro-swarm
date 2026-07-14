## 2026-07-12T10:31:43Z
Implement critical fixes based on Reviewer 1 and Reviewer 2 audits of cloud deployment and stealth reliability changes.
1. Requirements & Dependencies: Add psutil>=5.9.0 and duckduckgo-search>=6.0.0 to root requirements.txt and pyproject.toml.
2. Legacy DB Connection Pool Hardening in core/pg_sqlite_shim.py:
   - Import or copy format_neon_connection_string.
   - Target port 5432, -pooler suffix in host, sslmode=require&prepareThreshold=0.
   - Restrict limits (minconn=1, maxconn=3) for ThreadedConnectionPool.
   - Handle/clean raw URL query parameters not supported by psycopg2.
3. Clean up Redundant GitHub Keep-Alive Workflows: Delete .github/workflows/keep-alive.yml and .github/workflows/keep_alive.yml. Keep .github/workflows/keepalive.yml.
4. Neon DB Warmer Exit Status in core/neon_warmer.py: Exit status code 0 instead of 1 if DATABASE_URL is not set.
5. Proxy Validation Jitter and Timeout limits in core/ghost_hunter.py:
   - Limit validation loop to checking max 5 random proxies.
   - Defer duckduckgo_search import inside hunt_for_user method.
Verify: Compile checks, pytest, handoff.md in .agents/worker_cloud_stealth_reliability_remediation/handoff.md.

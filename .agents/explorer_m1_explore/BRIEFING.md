# BRIEFING — 2026-07-10T20:45:00Z

## Mission
Analyze codebase for cloud optimization sweep requirements (Single-Container Fusion, Edge-Cached Semantic Engine, Stealth Scraping, and SMTP/Telegram integration).

## 🔒 My Identity
- Archetype: explorer
- Roles: Teamwork explorer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_explore
- Original parent: 9ecfa312-3990-48cb-a356-7dc5df321cc7
- Milestone: explorer_m1_explore

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze start_cloud.py, Dockerfile.cloud, backend/celery_app.py, backend/tasks.py, backend/sync_worker.py, core/llm_provider_pool.py, backend/ai_engine.py, tests/test_llm_provider_pool.py, core/stealth_http.py, scrapers/stealth_ingest.py, core/free_smtp_pool.py, Telegram Bot config, backend/main.py, web/app_v2.py.

## Current Parent
- Conversation ID: 9ecfa312-3990-48cb-a356-7dc5df321cc7
- Updated: not yet

## Investigation State
- **Explored paths**: start_cloud.py, Dockerfile.cloud, backend/celery_app.py, backend/tasks.py, backend/sync_worker.py, backend/database.py, core/llm_provider_pool.py, core/semantic_cache.py, core/edge_cache.py, backend/ai_engine.py, core/ats_matcher.py, core/stealth_http.py, scrapers/stealth_ingest.py, core/stealth.py, core/free_smtp_pool.py, core/email_warmup.py, core/telegram/bot.py, core/telegram_bot.py, backend/main.py, web/app_v2.py.
- **Key findings**:
  - Celery solo pool and concurrency=1 can be configured via `start_cloud.py`'s Popen command line (adding `-P solo -c 1`).
  - Database connection pool sizes should be reduced to conserve memory under 512MB limit, and SQLite's `cache_size` should be set to -2000 or -4000 (currently set to -64000 = 64MB).
  - Caching is managed via `core/semantic_cache.py` (DB-based vector similarity search using Gemini text-embedding-004) and `core/edge_cache.py` (Upstash Redis REST API).
  - Cover letter generation in `backend/ai_engine.py` directly calls Groq and completely bypasses both the semantic cache and the LLM provider pool.
  - ATS matching in `core/ats_matcher.py` uses `LLMProviderPool` but doesn't implement edge caching (can be integrated with Upstash Redis by hashing resume+job text).
  - `core/stealth_http.py` uses `chrome110` by default but doesn't align custom headers, causing UA/JA3 mismatches. It also spawns a new session for every request (no keep-alive/cookie reuse).
  - `core/stealth.py` has a major bug: its `_BROWSER_PROFILES` uses unsupported strings like `"chrome131"`, which causes a crash inside `cffi_requests.AsyncSession()`.
  - `NodriverFallback` has a weak Canvas spoofing script that only modifies the first pixel, whereas `StealthScraper` defines a robust noise-addition script that is never injected.
  - The Telegram bot webhook is fully implemented in `web/app_v2.py` via `/webhook/telegram` but missing from `backend/main.py`. Polling mode runs as a separate process (consuming extra memory).
  - `core/email_warmup.py` is defined but never imported or used. `core/email_engine.py` implements a primitive local memory rate-limiting check instead.
- **Unexplored areas**: None, all items analyzed.

## Key Decisions Made
- Performed thorough, read-only exploration of all files.
- Verified test runs.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_explore\handoff.md — Handoff report of findings

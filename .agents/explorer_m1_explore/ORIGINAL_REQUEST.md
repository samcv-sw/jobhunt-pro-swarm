## 2026-07-10T20:44:59Z
You are an exploration agent. Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_explore.

Your task is to analyze the codebase for the cloud optimization sweep requirements:
1. Single-Container Web+Worker Fusion: Inspect start_cloud.py, Dockerfile.cloud, backend/celery_app.py, backend/tasks.py, and backend/sync_worker.py. How can we optimize memory footprint strictly under 512MB? Can we configure Celery to run with pool=solo and concurrency=1?
2. Edge-Cached Semantic Engine & Failover Pool: Inspect core/llm_provider_pool.py, backend/ai_engine.py, and tests/test_llm_provider_pool.py. Check where caching is configured and how we can integrate Upstash Redis for Cover Letter and ATS matching caching.
3. Stealth Scraping & TLS Fingerprinting: Inspect core/stealth_http.py and scrapers/stealth_ingest.py. How is curl_cffi configured? What are the missing parts for Chrome TLS JA3 spoofing and anti-bot bypasses?
4. SMTP Warmup & Telegram Webhook: Inspect core/free_smtp_pool.py and the Telegram Bot configuration (e.g. core/telegram/bot.py, backend/main.py, web/app_v2.py). How does the bot currently run? How can we migrate it to Webhooks in FastAPI? How does SMTP warmup run?

Perform a read-only code exploration. Do NOT edit any files. Deliver your findings in a structured report handoff.md in your working directory.

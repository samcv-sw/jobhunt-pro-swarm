# plan.md - Cloud Optimization, Caching, Stealth Scraping, and Webhooks

This document outlines the architecture, milestone decomposition, and interface contracts for optimizing JobHunt Pro to run under a $0 24/7 permanent cloud deployment strategy.

## Architecture
- **Web App / API Fusion Layer**: FastAPI web server (`web/app_v2.py`, `backend/main.py`) serving frontend templates, API endpoints, and a Telegram Bot webhook route.
- **Background Task Processing**: Fused single-container worker executing Celery tasks (`backend/tasks.py`) with memory optimizations (solo pool, low concurrency) and sync_worker loops.
- **LLM Failover Pool & Edge Cache**: AI Engine powered by `core/llm_provider_pool.py` leveraging Groq, Gemini API, and GitHub Models, edge-cached by Upstash Redis to deliver sub-100ms repeat requests.
- **Stealth Scraper**: Scraping client (`core/stealth_http.py`) utilizing `curl_cffi` to bypass Cloudflare/DataDome with Chrome JA3 TLS fingerprint spoofing and human emulation.
- **Messaging & Notifications**: Telegram Bot webhook receiver integrated directly into FastAPI, saving memory relative to standard long-polling.
- **SMTP Reputation**: Free SMTP pool warmup loop (`core/free_smtp_pool.py`) maintaining active sender credibility.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| 1 | M1: Single-Container Fusion & RAM Cap | Configure single-process container environment, optimize memory under 512MB using solo-pool Celery. | None | PLANNED |
| 2 | M2: Edge Cache & LLM Failover Pool | Integrate Upstash Redis for calculations caching. Implement failover pool (Groq, Gemini, GitHub Models) in `core/llm_provider_pool.py`. | M1 | PLANNED |
| 3 | M3: Stealth Scraping & TLS JA3 | Upgrade `core/stealth_http.py` with `curl_cffi` Chrome JA3 spoofing and bypasses. | None | PLANNED |
| 4 | M4: SMTP Warmup & Telegram Webhook | Implement warmup cron in `core/free_smtp_pool.py`. Migrate Telegram Bot to webhook integration in FastAPI app. | M1 | PLANNED |

## Interface Contracts
- **LLM Provider Pool API**:
  - `llm_pool.generate(prompt: str, system_instruction: str, ...) -> str` tries Groq -> Gemini -> GitHub Models.
- **Edge Cache API**:
  - Cache keys derived from inputs (e.g. SHA256 of resume + job description).
  - Retrieves from Upstash Redis; falls back to live calculation if cache miss.
- **Stealth HTTP Client**:
  - `stealth_http.get(url, **kwargs) -> Response` using `curl_cffi` spoofing `chrome120` or similar.
- **Telegram Webhook Route**:
  - `/api/v1/telegram/webhook` endpoint processing incoming Telegram updates.

## Verification Checklist

### M1: Single-Container Fusion & RAM Cap
- Dockerfile builds successfully.
- Command starts FastAPI, Celery (solo pool), and sync_worker in one container.
- Verification script runs under 512MB RAM.

### M2: Edge Cache & LLM Failover Pool
- `pytest tests/test_llm_provider_pool.py` passes.
- Test script shows cached calculations returned in < 100ms.
- LLM failover functions correctly on API provider key failure mock.

### M3: Stealth Scraping & TLS JA3
- HTTP requests via `core/stealth_http.py` successfully fetch from `https://bot.sannysoft.com/` without getting flagged.
- `curl_cffi` imports and executes cleanly.

### M4: SMTP Warmup & Telegram Webhook
- Warmup loop runs successfully.
- Webhook endpoints accept POST updates from Telegram.
- All 366+ tests pass successfully.

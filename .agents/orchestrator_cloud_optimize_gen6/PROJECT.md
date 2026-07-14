# PROJECT - JobHunt Pro Cloud Optimization & Reliability (Gen6)

This document outlines the architecture, milestones, interface contracts, and verification checklist for implementing 100% free (0 investment) 24/7 cloud optimization, performance, and reliability features (R1-R4) for JobHunt Pro.

## Architecture
- **Web App / API Layer**: FastAPI web server running inside a Docker container on Hugging Face Spaces (Docker CPU Basic, 2 vCPU, 16GB RAM).
- **Task Queue / Worker Layer**: Celery/background tasks running in the same Docker container or executed periodically via GitHub Actions scheduled runner cron.
- **Stealth Scrapers**: Playwright/Camoufox scrapers optimized to block images, fonts, media, and CSS stylesheets to reduce RAM and bandwidth usage.
- **Database / Cache Layer**: SQLite local fallback cache for Neon PostgreSQL, and thread-safe local cache to shield Upstash Redis from exceeding the 10k daily command limit.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | M1: Hugging Face Spaces Migration | Create Dockerfile for Hugging Face Spaces (install system requirements, Chrome/Chromium, dependencies, start FastAPI). | None | PLANNED |
| 2 | M2: GHA Scheduled Runner Cron | Configure `.github/workflows/scheduled_runner.yml` to run scraping/applying loop every 30 minutes. | None | PLANNED |
| 3 | M3: DB & Cache Rate-Limit Shield | Implement local thread-safe cache for Redis, and SQLite fail-safety fallback for Neon PG wakeup. | None | PLANNED |
| 4 | M4: Browser Scraper Optimization | Update Playwright/Camoufox scrapers to block heavy resources (images, fonts, stylesheets, trackers). | None | PLANNED |
| 6 | M6: AI Model Upgrades | Integrate fallback/rotation to Gemini 1.5 Pro and Claude 3.5 Sonnet API inside core LLM pool. | None | DONE |
| 7 | M7: Next.js Dashboard Analytics | Build interactive charts/statistics in Next.js frontend showing success metrics. | None | PLANNED |
| 8 | M8: Scraper Expansion | Add at least 3 new GCC/remote-focused boards (Bayt GCC, GulfTalent, etc.) to scraper pool. | None | PLANNED |
| 9 | M9: Auto-Fill Browser Agent | Implement automated browser autofill scripts for custom job application forms. | None | PLANNED |
| 10 | M10: WhatsApp Bot Remote Control | Add commands (/start, /pause, /status) to the WhatsApp bot to control campaigns. | None | PLANNED |
| 11 | M11: Verification & Test Suite | Run existing test suite (`pytest`) and verify all 403+ (or 431+) tests pass with no regressions. | M1-M10 | PLANNED |

## Interface Contracts
- **Hugging Face Docker**: FastAPI listens on port 7860 (Hugging Face standard port for web apps) and uses CPU-basic resources.
- **GHA Scheduled Runner**: Interacts with the backend via CLI runner script or HTTP API endpoints every 30 minutes.
- **Redis Cache Shield**: Wraps redis command execution in a local memory cache (e.g. dictionary or cachetools) before calling remote Upstash Redis.
- **Scraper Resource Blocker**: Uses Playwright route intercepting or Camoufox features to abort requests for resources of type `image`, `stylesheet`, `font`, `media`.

## Verification Checklist

### M1: Hugging Face Spaces Migration
- Dockerfile exists and builds successfully.
- Command for running FastAPI on port 7860 is set up.
- System dependencies (Chromium/Playwright) are installed in Dockerfile.

### M2: GHA Scheduled Runner Cron
- `.github/workflows/scheduled_runner.yml` exists and is syntactically valid.
- The workflow correctly triggers every 30 minutes or on push, running the scraping loop.

### M3: DB & Cache Rate-Limit Shield
- Verification that local cache intercepts Redis calls and returns cached values.
- Neon DB cold starts/timeouts are handled gracefully by SQLite queuing or retrying.

### M4: Browser Scraper Optimization
- Network requests for images, fonts, stylesheets, and media are blocked/aborted during scraping.
- Scraping executes successfully and saves structured data.

### M5: Verification & Test Suite
- `pytest` runs and passes all tests successfully.

# plan.md - Cloud Optimization & Reliability Enhancements (Gen 4)

This document outlines the architecture, milestone decomposition, and interface contracts for implementing zero-investment, 24/7 cloud optimization features (R1-R5) for JobHunt Pro.

## Architecture
- **Static Frontend**: Shifted to Cloudflare Pages (Free Tier), proxying API calls `/api/*` to the backend and offloading static asset hosting from the web container.
- **FastAPI / Web App**: High-performance API server (`backend/main.py`, `web/app_v2.py`) handling core requests and database integration.
- **Database Engine**: SQLAlchemy-powered database layer (`core/database.py`, `backend/database.py`) using Neon PG and local SQLite fallback, optimized with bulk insertions.
- **Stealth Scrapers**: Scraper clients (`core/stealth_http.py`, `scrapers/stealth_ingest.py`, etc.) hardened with platform-specific rate limits, anti-ban protections, and SSRF prevention.
- **Logging Pipeline**: Standard python logging configured to stream to Logtail/Better Stack (Free Tier) when a source token is present.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| 1 | M1: Cloudflare Pages Deployment | Configure static Next.js/Vue export targets and Pages routing headers. Enable static export output in `frontend/next.config.ts` and verify build. Update proxy headers for backend API calls. | None | PLANNED |
| 2 | M2: Platform-Specific Scraper Delays | Update `core/anti_ban.py` and `core/ban_shield.py` with adaptive delays and domain-specific limits (LinkedIn: 3s + jitter, Indeed: 1s, Bayt: 2s). | None | PLANNED |
| 3 | M3: Database Bulk Insertion | Refactor scraper modules (`scrapers/stealth_ingest.py`, `core/pa_job_scraper.py`, etc.) to use SQLAlchemy bulk inserts (`session.execute(insert(Model), [...])`) instead of loop-based row inserts. | None | PLANNED |
| 4 | M4: SSRF Prevention | Implement URL validation in `core/stealth_http.py` and scrapers to block private/local IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `0.0.0.0/8`). | None | PLANNED |
| 5 | M5: Persistent Logging to Logtail | Configure a Logtail syslog/HTTP handler in logging configurations (`start_cloud.py`, `backend/main.py`) activated by `LOGTAIL_SOURCE_TOKEN` env var. | None | PLANNED |

---

## Interface & Configuration Contracts

### 1. Cloudflare Pages & API Proxying
- Next.js Build preset: `Next.js (Static HTML Export)` with build command `npm run build` producing static files in `frontend/out` (or `frontend/.next`).
- Next.js Config: enable static export via `output: 'export'` or similar settings in `next.config.ts`.
- Proxy Headers: Cloudflare Pages `_headers` or functions (`_worker.js`) proxying `/api/*` to the FastAPI backend.

### 2. Platform-Specific Delays
- Configuration structure:
  ```python
  PLATFORM_DELAY_PROFILES = {
      "linkedin.com": {"delay": 3.0, "jitter": True},
      "indeed.com": {"delay": 1.0, "jitter": True},
      "bayt.com": {"delay": 2.0, "jitter": True},
      "default": {"delay": 1.5, "jitter": True}
  }
  ```
- Functions to modify: `core/anti_ban.py` and `core/ban_shield.py` should query this dictionary when determining sleep times.

### 3. Database Bulk Insertion
- Refactored pattern:
  ```python
  # Old:
  for job in jobs:
      session.add(Job(**job))
  session.commit()
  
  # New:
  from sqlalchemy import insert
  session.execute(insert(Job), jobs)
  session.commit()
  ```

### 4. SSRF Prevention
- Function: `is_safe_url(url: str) -> bool`
- Check target: Resolve domain to IP addresses, check if any IP falls within private network segments (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `0.0.0.0/8`).

### 5. Logtail Logger
- Package: `logtail-python` or standard HTTP request sending logs to `https://in.logs.betterstack.com`.
- Initialization:
  ```python
  if os.getenv("LOGTAIL_SOURCE_TOKEN"):
      # Add LogtailHandler to the root logger
  ```

---

## Verification Checklist

### M1: Cloudflare Pages Deployment
- Static export build finishes successfully using `npm run build`.
- Verification that `/api/*` requests route dynamically to the backend API.

### M2: Platform-Specific Scraper Delays
- Custom tests verify that LinkedIn queries introduce a ~3s delay, Indeed ~1s, and Bayt ~2s.

### M3: Database Bulk Insertion
- Scraping tests run successfully.
- Code inspection verifies bulk inserts are used.

### M4: SSRF Prevention
- URL validation throws `ValueError` or `HTTPException` when requesting `http://127.0.0.1:8000/` or `http://192.168.1.1/`.
- Safe public URLs pass validation.

### M5: Persistent Logging to Logtail
- Test logs sent to Logtail API endpoint return HTTP 202/200 when a mock token is provided.

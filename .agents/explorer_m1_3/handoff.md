# Handoff Report — Explorer M1-3: Multi-Region Keepalive Sentinels

## 1. Observation

### 1.1 Cloudflare Worker Keepalive (`cloudflare/keepalive_cron/`)
- In `cloudflare/keepalive_cron/wrangler.toml` (lines 5–10):
  ```toml
  [vars]
  APP_URL = "https://jobhunt-pro.onrender.com/"
  ENGINE_URL = "https://jobhunt-pro-engine.onrender.com/"

  [triggers]
  crons = ["*/5 * * * *"]
  ```
  Direct observation: The cron cadence is set to `*/5 * * * *` (5 minutes) instead of the 4-minute cadence required by Milestone M1 Feature 3. The variables point to root `/` rather than `/ping`.
- In `cloudflare/keepalive_cron/src/index.js` (lines 3–21):
  ```javascript
  const urls = [
    env.APP_URL || 'https://jobhunt-pro.onrender.com/',
    env.ENGINE_URL || 'https://jobhunt-pro-engine.onrender.com/'
  ];
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'User-Agent': 'Cloudflare-Worker-KeepAlive-Cron'
    }
  });
  ```
  Direct observation: `fetch()` calls do not specify an `AbortSignal.timeout(...)`, hitting base URLs (`/`) which triggers full template rendering rather than fast zero-DB `/ping` responses.

### 1.2 GitHub Actions Workflows (`.github/workflows/`)
- `.github/workflows/cloud_keepalive_247.yml` runs `scripts/cron_keepalive.py` every 5 min (`cron: '*/5 * * * *'`) with endpoints:
  ```yaml
  PRIMARY_API_URL: ${{ secrets.PRIMARY_API_URL || 'https://jobhunt-pro.onrender.com/healthz' }}
  BACKEND_API_URL: ${{ secrets.BACKEND_API_URL || 'https://jhfguf.pythonanywhere.com/api/v1/health' }}
  KOYEB_API_URL: ${{ secrets.KOYEB_API_URL || 'https://jobhunt-pro-koyeb.koyeb.app/healthz' }}
  ```
- `.github/workflows/render-fallback.yml` monitors PA (`https://${DOMAIN}/api/ping`), and if status != 200, automatically deploys Render fallback and alerts Telegram.
- `.github/workflows/smart-tick.yml` runs every 5 minutes, checks `https://${PA_DOMAIN}/api/v2/health`, and reloads the webapp via PythonAnywhere Webapp Reload API if unhealthy.
- Additional keepalive workflows exist: `keepalive.yml`, `keep_alive.yml`, `keepalive_ultra_247.yml`, and `cloud_keepalive_and_swarm.yml`.

### 1.3 Python Sentinel Scripts (`scripts/`)
- `scripts/cloud_keepalive_247.py` (lines 25–54, 79–83):
  - `ping_endpoint(url, timeout_seconds=10.0)` sets `User-Agent: JobHuntPro-KeepAlive/2.0`, supports `httpx` with `urllib` fallback.
  - CLI defaults: `--url http://localhost:8000/api/health`, `--interval 300` (5 minutes).
  - `send_telegram_fallback(message)` sends Telegram alert when ping fails.
- `scripts/cron_keepalive.py` (lines 13–39):
  - Concurrently pings `PRIMARY_API_URL` (`https://jobhunt-pro.onrender.com/healthz`), `BACKEND_API_URL` (`https://jhfguf.pythonanywhere.com/api/v1/health`), and `KOYEB_API_URL` (`https://jobhunt-pro-koyeb.koyeb.app/healthz`) with 12s timeout and `User-Agent: JobHuntPro-KeepAlive-Swarm/2026.2`.
- `scripts/cloud_keepalive.py` (lines 17–19):
  - Pings `https://jhfguf.pythonanywhere.com/ping` every 4 minutes (240s) with 10s timeout.

### 1.4 Test Coverage in `tests/`
- Direct observation: Existing test suite includes `tests/test_m1_health.py`, `tests/test_m1_health_failures.py`, `tests/test_deep_health.py`, and `tests/test_health_monitor.py`.
- No test files currently exist in `tests/` covering `scripts/cloud_keepalive_247.py` or `scripts/cron_keepalive.py`.

---

## 2. Logic Chain

1. **Premise 1 (Idle Spin-Down Prevention)**: Micro-VM free tiers (e.g. Render, Koyeb, Fly.io) spin down after 5–15 minutes of inactivity. To guarantee 24/7 zero-downtime availability, keepalive sentinels must execute at a 4-minute cadence (`*/4 * * * *`).
2. **Premise 2 (Resource Efficiency & Zero Lock)**: Keepalive sentinels should target lightweight zero-DB endpoints (`/ping`, `/api/ping`, `/healthz`) which respond in <5ms without acquiring SQLite/Postgres locks or rendering HTML templates.
3. **From Observation 1.1 & 1.2**: `cloudflare/keepalive_cron/wrangler.toml` is configured for 5-minute cron (`*/5 * * * *`) and `src/index.js` pings root `/` instead of `/ping`, lacking fetch timeouts and fallback endpoints.
4. **From Observation 1.3**: `scripts/cloud_keepalive_247.py` defaults to 300s interval and a single target URL (`/api/health`), whereas `scripts/cron_keepalive.py` already supports multi-cloud endpoints (`Render`, `PA`, `Koyeb`).
5. **From Observation 1.4**: While server health endpoints have failure tests (`test_m1_health_failures.py`), the keepalive sentinel scripts (`cloud_keepalive_247.py`, `cron_keepalive.py`) and fast `/ping` route contract lack dedicated unit tests.
6. **Conclusion**: Aligning `cloudflare/keepalive_cron/` to 4-minute cron targeting `/ping` with timeout + fallback endpoints, updating `cloud_keepalive_247.py` defaults, and creating `tests/test_keepalive_sentinels.py` will fully complete Feature 3 acceptance criteria.

---

## 3. Caveats

1. **GitHub Actions Cron Precision**: GitHub Actions scheduled cron jobs can experience variable queue delays (2–10 min) during peak GitHub infrastructure load. Therefore, Cloudflare Worker cron (`cloudflare/keepalive_cron/`) serves as the strict, high-precision 4-minute primary sentinel.
2. **DNS & Network Reachability**: Remote keepalive sentinels depend on external public DNS resolution. Test suites should mock HTTP/network calls to avoid depending on live remote network access during CI.
3. **No Code Written to Application Core**: As Explorer, this investigation is strictly read-only; proposed code updates and test blueprints are provided for the implementation phase.

---

## 4. Conclusion

- **Status of Multi-Region Keepalive Sentinels**: The architecture has extensive multi-cloud infrastructure already in place (Render, PythonAnywhere, Koyeb, Fly.io, Cloudflare, HuggingFace), with automated failover (`render-fallback.yml`) and self-reload (`smart-tick.yml`).
- **Required Action Items for Implementer**:
  1. Update `cloudflare/keepalive_cron/wrangler.toml`: Set `crons = ["*/4 * * * *"]` and configure `PRIMARY_URL`, `BACKEND_URL`, `KOYEB_URL` targeting `/ping`.
  2. Update `cloudflare/keepalive_cron/src/index.js`: Target `/ping` with `AbortSignal.timeout(10000)` and multi-endpoint fallback.
  3. Update `scripts/cloud_keepalive_247.py`: Set default interval to 240s, default URL to `/ping`, and add multi-endpoint fallback support.
  4. Create `tests/test_keepalive_sentinels.py`: Add unit tests for `scripts/cloud_keepalive_247.py` (`ping_endpoint`, timeout, Telegram alert), `scripts/cron_keepalive.py` (`ping_target`, multi-cloud gather), and FastAPI zero-DB `/ping` endpoint contract.

---

## 5. Verification Method

To independently verify these findings:
1. Inspect files:
   - `cloudflare/keepalive_cron/wrangler.toml` (check line 10 for cron expression)
   - `cloudflare/keepalive_cron/src/index.js` (check lines 3–20 for target URLs and fetch options)
   - `scripts/cloud_keepalive_247.py` (check lines 25–54, 80–83)
   - `scripts/cron_keepalive.py` (check lines 13–17)
2. Run test verification (once implemented):
   ```bash
   pytest tests/test_keepalive_sentinels.py tests/test_m1_health.py tests/test_m1_health_failures.py -v
   ```
3. Test dry-run CLI:
   ```bash
   python scripts/cloud_keepalive_247.py --url https://jhfguf.pythonanywhere.com/ping --dry-run
   ```

# Self-Healing Cloud Architecture — Deployment Summary
**Date**: 2026-06-23
**Project**: JobHunt Pro (C:\Users\samde\Desktop\cv sam new ma3 kimi)

## Files Created

### 1. `.github/workflows/self-heal.yml` (9,973 bytes)
Master self-healing workflow running every 5 minutes:
- Check PA health via `/api/ping` (measuring response time in ms)
- If PA down: triggers `pa-reload.yml` workflow + direct PA API reload
- If PA slow (>3s): sends Telegram alert
- If GHA quota exceeded: switches to Render/Cloudflare fallback
- Calls `/api/system/auto-heal` on PA for internal healing
- Hourly summary job: fetches stats from `/api/system/status` and sends to Telegram (total apps, emails, errors)

### 2. `.github/workflows/mega-tick.yml` (8,926 bytes)
Maximum throughput tick every 2 minutes:
- Pre-flight PA health check
- 3 retry attempts with exponential backoff (0s → 2s → 4s)
- 240s timeout per attempt
- Calls `/api/v2/cloud-tick` with `company_limit=15`
- If all 3 attempts fail: auto-reloads PA via `PA_API_TOKEN`
- Telegram notification on EVERY tick with detailed stats (attempts, duration, HTTP code, mode)

### 3. `.github/workflows/render-fallback.yml` (7,131 bytes)
Render.com fallback deployment:
- Verifies PA is actually down before deploying
- Auto-generates `render.yaml` with proper PythonAnywhere-compatible config
- Deploys via Render API or deploy hook
- Telegram notification on activation
- Waits up to 90s for Render to come up with 5 retry attempts
- Verifies both PA and Render status before exiting

### 4. `core/auto_heal.py` (24,853 bytes)
Self-healing Python module (Pure asyncio, no subprocess):

**Checks (every 60s)**:
1. **RAM usage** — reads `/proc/meminfo` or `psutil`, auto-reloads PA if >90%
2. **Stuck campaigns** — resets campaigns in 'running' state for >30 minutes
3. **Dead locks** — removes lock entries older than 1 hour
4. **SMTP rate limiting** — rotates SMTP accounts if any exceed 100 sends/hour
5. **Groq API key** — validates key health via models list endpoint

**Architecture**:
- `asyncio` background loop — never spawns subprocesses (PA-free-tier compatible)
- Thread-safe state with `threading.Lock`
- Heal history persisted to `data/auto_heal_history.json` (last 500 entries)
- Telegram alerting via HTTP (no external libraries beyond `requests`/`httpx`)
- Lazy DB imports to avoid circular dependencies

**Exports**: `run_heal_cycle()`, `start_background_monitor()`, `start_background_monitor_sync()`, `get_heal_state()`, `get_system_health_snapshot()`

### 5. `web/app_v2.py` — Updated
Three new/updated endpoints appended:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/ping` | GET | Fast health check (<100ms) — alive + uptime |
| `/api/system/status` | GET | Full system status: RAM, campaigns active, emails sent today, API keys, SMTP, heal state |
| `/api/system/auto-heal` | POST | Trigger heal cycle (accepts `{"force": true}` for forced heal) |

**Import added**: `from core import auto_heal as _autoheal`

## Validation
- `web/app_v2.py`: Python syntax check PASSED (AST parse)
- `core/auto_heal.py`: Python syntax check PASSED (AST parse)
- All 3 YAML workflows: structurally valid (name/on/jobs present)
- No duplicate endpoints (single `/api/ping` at line ~2201)

## Key Design Decisions
1. **$0 budget compliance**: Uses only free tiers — GHA schedule (5min), Render free (auto-sleeps), Telegram bot API
2. **PythonAnywhere constraints**: No subprocess; asyncio only; 250s max request time honored
3. **Redundancy**: Three-layer fallback: PA → GHA self-heal → Render → Cloudflare
4. **Non-blocking alerts**: Telegram sends use `asyncio.to_thread()` to avoid blocking event loop

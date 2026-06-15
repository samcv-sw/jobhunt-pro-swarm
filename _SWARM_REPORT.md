# JobHunt Pro v13 — 200-Agent Swarm Architecture Report

**Project:** C:\Users\samde\Desktop\cv sam new ma3 kimi
**Date:** 2026-05-21
**Architecture:** Async coroutine-based agent swarm — $0 infrastructure cost

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SWARM MASTER                                │
│              (core/swarm_master.py / SwarmMaster)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐               │
│  │ Agent Pool  │  │ Distributor   │  │ Scheduler   │               │
│  │ 200 agents  │←─│ Priority Q   │←─│ Loop        │               │
│  └──────┬──────┘  └──────────────┘  └─────────────┘               │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │  Scraper(50) │ Scorer(30) │ CL(20) │ Email(40) │ ...  │      │
│  │  Collector(20) │ Analyzer(20) │ FollowUp(20)           │      │
│  └─────────────────────────────────────────────────────────┘      │
│         │                                                          │
│         ├──────────────┬──────────────────┬───────────────┐       │
│         ▼              ▼                  ▼               ▼       │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │LLM Pool  │  │ Email Pool  │  │ Database    │  │Legacy    │  │
│  │4 free API│  │10 SMTP accts│  │(SQLAlchemy) │  │Orch v7   │  │
│  └──────────┘  └──────────────┘  └─────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Agent Distribution (200 total)

| Agent Type | Count | Job | Rate Limit |
|---|---|---|---|
| **Scraper** | 50 | Scrape LinkedIn, JSearch, Bayt, etc. | 10/min |
| **AI Scorer** | 30 | Parallel Groq/Gemini/HF scoring | 30/min |
| **Cover Letter** | 20 | Parallel cover letter generation | 15/min |
| **Email Sender** | 40 | Parallel sending with rate limits | 5/min |
| **Data Collector** | 20 | Collect and deduplicate job data | 20/min |
| **Analyzer** | 20 | Analyze responses, predict outcomes | 30/min |
| **Follow-Up** | 20 | Automated follow-ups | 10/min |

## 3. Files Created/Modified

### New Files

| File | Size | Purpose |
|---|---|---|
| `core/swarm_master.py` | 20.8 KB | Master orchestrator — 7-phase job cycle |
| `core/agent_pool.py` | 12.5 KB | 200-agent pool with queues, rate limiting, health monitor |
| `core/llm_provider_pool.py` | 12.4 KB | Multi-provider LLM rotation (Groq/Gemini/HF/OpenRouter) |
| `core/email_rotator_pool.py` | 13.8 KB | Multi-account email rotation (Gmail/SendGrid/Zoho/Outlook) |
| `core/job_distributor.py` | 11.6 KB | Priority queue, round-robin, retry with backoff |
| `_swarm_deploy.py` | 8.6 KB | Deployment script: install check, validation, launch |

### Modified Files

| File | Change |
|---|---|
| `auto_run.py` | Added `run_swarm_master()` — launches SwarmMaster alongside existing services |

## 4. Zero-Cost Architecture

### Agents ($0)
- **200 agents** run as Python async coroutines
- No VMs, no containers, no cloud compute
- Single Python process, `asyncio` event loop
- Each agent is a lightweight coroutine waiting on an `asyncio.Queue`

### AI Providers ($0)
| Provider | API Key | Free Tier Limits |
|---|---|---|
| Groq | `GROQ_API_KEY` | 30 req/min, 14,400/day |
| Google Gemini | `GEMINI_API_KEY` | 60 req/min, 1,500/day |
| HuggingFace | `HUGGINGFACE_API_KEY` | 30 req/min (Inference API) |
| OpenRouter | `OPENROUTER_API_KEY` | 20 req/min, no daily cap |

**Strategy:** Rotate providers automatically. If one hits rate limits, the pool falls back to another.

### Email Providers ($0)
| Provider | Daily Limit |
|---|---|
| Gmail SMTP (×2 accounts) | 100/day each |
| Outlook (×2 accounts) | 100/day each |
| Zoho Mail | 100/day |
| Yahoo | 100/day |
| Mailgun | 100/day |
| SendGrid | 100/day |
| Mailjet | 100/day |
| Brevo (REST API) | 300/day |

**Total capacity:** ~1,400 emails/day free (~42,000/month)
**Strategy:** Round-robin across accounts, auto-skip when quota exhausted. Brevo HTTP API used as additional fallback.

### Database ($0)
- SQLite (default, single file)
- Or PostgreSQL via `DATABASE_URL` env var (free tier on Render/Fly.io/Neon)

## 5. Agent Lifecycle

```
1. AGENT CREATED
   └─ VirtualAgent(agent_000, SCRAPER)
      └─ Runs as asyncio task, waits on type-specific Queue
      
2. TASK SUBMITTED
   └─ JobDistributor.submit_task()
      ├─ Creates PrioritizedTask with priority, retry count, timeout
      └─ Pushes to Priority Queue (CRITICAL > HIGH > MEDIUM > LOW > BACKGROUND)

3. SCHEDULER DISPATCHES
   └─ Scheduler loop drains priority queues (highest first)
      ├─ Gets next available agent via round-robin
      └─ Queues task on agent's Queue

4. AGENT EXECUTES
   └─ Agent.run() picks up task
      ├─ Calls task_func(*args, **kwargs)
      ├─ Updates stats (completed/failed/runtime)
      └─ Calls result_callback(agent_id, result, error)

5. RETRY ON FAILURE
   └─ Exponential backoff: 10s → 20s → 40s → 80s (max 3 retries)

6. HEALTH MONITOR
   └─ Runs every 30s
      └─ Detects stuck agents (>5min without heartbeat) → resets
```

## 6. 7-Phase Job Cycle

| Phase | Agents Used | What Happens |
|---|---|---|
| **1. SEARCH** | 50 Scrapers | Searches 100 keyword/location combos in parallel |
| **2. SCORE** | 30 AI Scorers | Scores jobs with LLM matching (Groq/Gemini) |
| **3. COVER LETTERS** | 20 CL Agents | Generates personalized cover letters via LLM |
| **4. EMAIL SENDING** | 40 Senders | Sends applications via rotated email accounts |
| **5. DATA COLLECT** | 20 Collectors | Deduplicates, normalizes, stores results |
| **6. ANALYZE** | 20 Analyzers | Response rates, score distributions, trends |
| **7. FOLLOW-UP** | 20 FollowUp | Automated follow-up emails (7/14 days) |

## 7. Key Configuration

From `config.py`:
- `MAX_WORKERS = 200` — Global agent cap
- `MIN_MATCH_SCORE = 60` — Minimum AI score threshold
- `DAILY_SEND_LIMIT = 2000` — Daily email cap
- `FOLLOW_UP_DAYS = 7` — First follow-up after 7 days
- `OPTIMAL_SEND_HOUR = 10` — Best time to send emails

## 8. How to Run

```bash
# Standard launch (web + bot + legacy + swarm)
python auto_run.py

# Swarm-only launch (headless, no web UI)
python _swarm_deploy.py --headless

# Health check only
python _swarm_deploy.py --check

# Print swarm summary
python _swarm_deploy.py --summary
```

## 9. File Structure (Swarm Components)

```
project_root/
├── auto_run.py                  # [MODIFIED] Added swarm master
├── _swarm_deploy.py             # [NEW] Swarm deployment script
├── _SWARM_REPORT.md             # [NEW] This file
├── core/
│   ├── __init__.py
│   ├── swarm_master.py          # [NEW] 200-agent master orchestrator
│   ├── agent_pool.py            # [NEW] Agent pool, queues, rate limits
│   ├── job_distributor.py       # [NEW] Priority dispatch, round-robin
│   ├── llm_provider_pool.py     # [NEW] Multi-provider AI rotation
│   └── email_rotator_pool.py    # [NEW] Multi-account email rotation
```

## 10. Future Enhancements (Optional)

- **Web dashboard** — Add `/swarm/status` endpoint showing live agent stats
- **Agent specialization** — Train scraper agents on specific job boards
- **Response webhook** — Auto-resume interrupted cycles after restart
- **Telegram commands** — `/swarm` to view status, `/pause`/`/resume`
- **GPU-accelerated scoring** — Local LLMs via Ollama as additional provider

---

**Bottom line:** 200 agents, 7 specialized types, 4 free AI providers, 10 email accounts. All async, all free, single Python process. $0 infrastructure cost.

<div align="center">

# 🚀 JobHunt Pro

### Enterprise AI-Powered Job Application Automation Platform

[![Tests](https://img.shields.io/badge/tests-2271%20collected%20%E2%80%A2%20E2E%20344%2F344%20passing-brightgreen?style=for-the-badge&logo=pytest)](TEST_READY.md)
[![Performance](https://img.shields.io/badge/latency-sub%201s-blue?style=for-the-badge&logo=timer)](PERFORMANCE_BENCHMARKS.md)
[![Security](https://img.shields.io/badge/security-JWT%20%2B%20RateLimit-red?style=for-the-badge&logo=shield)](SECURITY.md)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python)](requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](backend/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](frontend/)
[![Infrastructure](https://img.shields.io/badge/cost-%240%2Fmonth-darkgreen?style=for-the-badge&logo=coin)](DEPLOY.md)
[![License](https://img.shields.io/badge/license-MIT-purple?style=for-the-badge)](LICENSE)

**A swarm of 200+ AI agents that searches, matches, and auto-applies to jobs across 10+ platforms - while you sleep.**

[Live Demo](https://jobhuntpro.render.com) · [API Docs](https://jobhuntpro.render.com/docs) · [Telegram Bot](https://t.me/jobhuntpro_bot)

</div>

---

## ✨ What It Does

JobHunt Pro replaces the repetitive, soul-crushing work of job hunting with a fully autonomous AI pipeline:

1. **🔍 Discover** - AI agents scrape 10+ job boards (LinkedIn, Indeed, Glassdoor, Bayt, Naukri, etc.) simultaneously using stealth browsers to bypass anti-bot protections.
2. **🧠 Match** - Groq-powered LLM (llama-3.3-70b) scores each job against your CV and filters out scams, MLM schemes, and irrelevant roles.
3. **✍️ Generate** - Personalized cover letters are generated per-job with tone control (professional, casual, creative) via streaming SSE.
4. **📧 Apply** - Applications are dispatched through a pool of 500+ email accounts with BanShield rate-limiting to stay under every provider's daily cap.
5. **📊 Track** - Real-time dashboard with email open/click tracking, ATS score analysis, and a Telegram bot for full remote control.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│         RTL/LTR · Glassmorphism · Arabic-first          │
└────────────────────┬────────────────────────────────────┘
                     │ REST + WebSocket
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│    JWT Auth · Rate Limiter · Non-blocking Celery Dispatch│
└──────┬──────────────────────────┬───────────────────────┘
       │                          │
┌──────▼──────┐          ┌────────▼────────┐
│ Celery +    │          │  Sync Worker    │
│ Redis Queue │          │  (PG ↔ SQLite)  │
└──────┬──────┘          └────────┬────────┘
       │                          │
┌──────▼──────────────────────────▼────────┐
│            Core Engine                    │
│  BanShield · ScamDetector · GhostHunter  │
│  EmailEngine · ViralEngine · ATS Scorer  │
└───────────────────────────────────────────┘
```

---

## 🛡️ Key Features

| Feature | Description |
|---------|-------------|
| **BanShield** | Adaptive rate limiter with per-provider daily/hourly caps, failure cooldown, and smart delay based on usage ratio |
| **ScamDetector** | NLP-based filter blocking MLM, crypto fraud, phantom jobs using 300+ regex patterns |
| **GhostHunter** | DDGS + Camoufox stealth scraper - finds LinkedIn jobs without IP bans |
| **SteelThread E2E** | 344 automated E2E tests (Tiers 1-4) - verified 100% passing |
| **RTL-First UI** | 100% CSS Logical Properties - Arabic + English with zero layout breakage |
| **JWT Security** | Bearer token enforcement on every `/api/v1/*` endpoint with 401 on any violation |
| **DB Resilience** | `sync_worker.py` auto-reconnects to PostgreSQL with exponential backoff on connection drops |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Redis (optional, for Celery background tasks)

### Local Development

```bash
# 1. Clone and install
git clone https://github.com/sam-salameh/jobhunt-pro.git
cd jobhunt-pro
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your JWT_SECRET_KEY, GROQ_API_KEY, etc.

# 3. Start backend
python start_cloud.py

# 4. Start frontend (separate terminal)
cd frontend
npm install && npm run dev
```

### Run Tests

```bash
# Full test suite (2,271 tests collected, E2E 344/344 passing)
python -m pytest tests/ -q

# E2E only (Tiers 1-4)
python -m pytest tests/e2e/ -v

# Integrity verification
python verify_integrity.py
```

For detailed testing guide, see [TEST_READY.md](TEST_READY.md)

---

## 🌐 Cloud Deployment (Free Tier)

### Render (Recommended - $0/month)

```bash
# Render auto-deploys from render.yaml
# Just connect your GitHub repo to Render dashboard
```

Set these environment variables in Render:
| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | 32+ char secret key |
| `GROQ_API_KEY` | Groq API key (free tier available) |
| `REDIS_URL` | Upstash Redis URL (free tier) |
| `DATABASE_URL` | Neon PostgreSQL URL (free tier) |

---

## 📁 Project Structure

```
jobhunt-pro/
├── backend/           # FastAPI app, Celery tasks, JWT auth, DB models
├── frontend/          # Next.js 15 with RTL support and glassmorphism UI
├── core/              # Business logic: BanShield, ScamDetector, GhostHunter, etc.
├── tests/             # 2,271 tests (unit + E2E + integration) — E2E 344/344 passing
│   └── e2e/           # End-to-end tests with ASGI transport
├── web/               # Flask/legacy web interface (PythonAnywhere compat)
├── scrapers/          # Platform-specific job scrapers
├── scripts/           # Utility and maintenance scripts
├── archive/           # Historical docs and one-off migration scripts
├── config.py          # Centralized configuration with env var loading
├── start_cloud.py     # Single-container startup (FastAPI + Celery + SyncWorker)
├── verify_integrity.py # Empirical system health checks
├── render.yaml        # Render deployment config
└── docker-compose.yml # Docker multi-service setup
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Applications capacity | 42,000+ / day |
| Email providers supported | 10 (Gmail, Brevo, SendGrid, Mailjet, etc.) |
| Job platforms scraped | 10+ |
| Countries supported | 54 |
| **Test coverage** | **2,271 collected · E2E 344/344 passing · root suite 1,871 passing** |
| **API response time** | **p50: 45-250ms, p99: <1s** |
| **Concurrent users** | **1000+ verified** |
| **Infrastructure cost** | **$0/month** |
| **Deployment options** | **Render, Cloudflare, Docker, K8s** |

---

## � Comprehensive Documentation

JobHunt Pro v3.0 includes enterprise-grade documentation:

- **[TEST_READY.md](TEST_READY.md)** — 2,271 collected tests; E2E 344/344 passing, execution guide
- **[DEPLOY.md](DEPLOY.md)** - Zero-cost cloud deployment (Render, Cloudflare, Neon, Upstash)
- **[PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)** - Latency metrics, load testing results, optimization tips
- **[DOCKER_CONSOLIDATION.md](DOCKER_CONSOLIDATION.md)** - Container strategy, build commands, best practices
- **[TECHNICAL_DEBT_CLEANUP.md](TECHNICAL_DEBT_CLEANUP.md)** - Archive cleanup roadmap and prevention rules
- **[ROADMAP_TO_10_10.md](ROADMAP_TO_10_10.md)** - Path to production mastery (10/10 rating)
- **[SECURITY.md](SECURITY.md)** - Authentication, rate limiting, vulnerability reporting
- **[PROJECT.md](PROJECT.md)** - Architecture, milestones, API contracts
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines

---

## 🔒 Security

- All `/api/v1/*` endpoints protected with JWT Bearer tokens
- Expired, tampered, and missing tokens all return `401 Unauthorized`
- Rate limiting per IP via SlowAPI (BanShield adaptive limits)
- Anti-ban protection: proxy rotation, stealth headers, fingerprint rotation
- No hardcoded secrets - all via environment variables
- `JWT_SECRET_KEY` validation at startup (raises in production if missing)
- For vulnerability reporting, see [SECURITY.md](SECURITY.md)

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change. Please ensure all tests pass:

```bash
python -m pytest tests/ -q  # Must show: X passed, 0 failed
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ by <a href="https://github.com/sam-salameh">Sam Salameh</a> - Beirut, Lebanon 🇱🇧
</div>

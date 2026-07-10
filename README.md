<div align="center">

# 🚀 JobHunt Pro

### Enterprise AI-Powered Job Application Automation Platform

[![Tests](https://img.shields.io/badge/tests-403%20passed-brightgreen?style=for-the-badge&logo=pytest)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python)](requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](backend/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](frontend/)
[![License](https://img.shields.io/badge/license-MIT-purple?style=for-the-badge)](LICENSE)

**A swarm of 200+ AI agents that searches, matches, and auto-applies to jobs across 10+ platforms — while you sleep.**

[Live Demo](https://jobhuntpro.render.com) · [API Docs](https://jobhuntpro.render.com/docs) · [Telegram Bot](https://t.me/jobhuntpro_bot)

</div>

---

## ✨ What It Does

JobHunt Pro replaces the repetitive, soul-crushing work of job hunting with a fully autonomous AI pipeline:

1. **🔍 Discover** — AI agents scrape 10+ job boards (LinkedIn, Indeed, Glassdoor, Bayt, Naukri, etc.) simultaneously using stealth browsers to bypass anti-bot protections.
2. **🧠 Match** — Groq-powered LLM (llama-3.3-70b) scores each job against your CV and filters out scams, MLM schemes, and irrelevant roles.
3. **✍️ Generate** — Personalized cover letters are generated per-job with tone control (professional, casual, creative) via streaming SSE.
4. **📧 Apply** — Applications are dispatched through a pool of 500+ email accounts with BanShield rate-limiting to stay under every provider's daily cap.
5. **📊 Track** — Real-time dashboard with email open/click tracking, ATS score analysis, and a Telegram bot for full remote control.

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
| **GhostHunter** | DDGS + Camoufox stealth scraper — finds LinkedIn jobs without IP bans |
| **SteelThread E2E** | 403 automated tests covering auth, scraping, cover letters, CI/CD, and billing |
| **RTL-First UI** | 100% CSS Logical Properties — Arabic + English with zero layout breakage |
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
# Full test suite (403 tests)
python -m pytest tests/ -q

# E2E only
python -m pytest tests/e2e/ -q

# Integrity verification
python verify_integrity.py
```

---

## 🌐 Cloud Deployment (Free Tier)

### Render (Recommended — $0/month)

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
├── tests/             # 403 automated tests (unit + E2E + integration)
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
| Test coverage | 403 tests, 0 failures |
| API response time | < 50ms (Celery dispatch non-blocking) |

---

## 🔒 Security

- All `/api/v1/*` endpoints protected with JWT Bearer tokens
- Expired, tampered, and missing tokens all return `401 Unauthorized`
- Rate limiting per IP via `SlowAPI`
- No hardcoded secrets — all via environment variables
- `JWT_SECRET_KEY` validation at startup (raises in production if missing)

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change. Please ensure all tests pass:

```bash
python -m pytest tests/ -q  # Must show: X passed, 0 failed
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ by <a href="https://github.com/sam-salameh">Sam Salameh</a> — Beirut, Lebanon 🇱🇧
</div>

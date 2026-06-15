---
title: JobHunt SaaS
emoji: 🦀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# JobHunt Pro - Maximum Power SaaS

> **Autonomous Job Application Engine — 200 Agents, 19 Providers, $0 Investment**

Apply to 2,100+ jobs while you sleep. 200 swarm agents. 19 email providers. Cyberpunk dashboard. Runs forever on free cloud.

---

## What It Does

```
You run: python auto_run.py
System does:
  1. Searches 55 job titles across 71 locations
  2. Finds company email addresses
  3. Generates personalized cover letters
  4. Sends applications via 19 SMTP providers
  5. Follows up after 4/7/14 days
  6. Parses responses (interview/rejection/offer)
  7. Auto-replies to interviews with Calendly link
  8. Negotiates salary when offer detected
```

---

## Features

| Feature | Status |
|---------|--------|
| 200-agent swarm | ✅ Working |
| 19 email providers | ✅ Configured |
| Cyberpunk dashboard | ✅ Built |
| Cover letter generator | ✅ 3 templates |
| Salary negotiation AI | ✅ Auto-draft |
| Resume optimizer | ✅ Scoring system |
| LinkedIn automation | ✅ Connection requests |
| Job board aggregator | ✅ 5 boards |
| Anti-ghosting follow-ups | ✅ 3 follow-ups |
| Response parser | ✅ Interview/rejection/offer |
| Email tracking | ✅ Open/click detection |
| Compliance engine | ✅ GDPR/GCC |
| Premium SaaS tiers | ✅ 4 tiers ($0/$29/$79/$199) |
| Cloud deployment | ✅ Docker + Kubernetes |
| Dry-run mode | ✅ Save emails to files |

---

## Quick Start

### Step 1: Run Locally
```bash
cd "C:\Users\samde\Desktop\cv sam new ma3 kimi"
python auto_run.py
```

### Step 2: Open Dashboard
```
http://localhost:8000/dashboard
```

### Step 3: Check Health
```
http://localhost:8000/health
```

### Step 4: Deploy to Cloud (Free)
```bash
# Oracle Cloud Always Free — $0/month
# See FREE_CLOUD_DEPLOY.md for step-by-step guide
deploy_free.bat
```

---

## System Specs

```
Agents:        200 concurrent
Providers:     19 SMTP (10 configured)
Job Titles:    55 search queries
Locations:     71 target regions
Companies:     47 premium employers
Daily Limit:   2,100 emails
Follow-ups:    3 per application
AI Models:     Gemini + Groq (optional)
Database:      PostgreSQL / SQLite
Cache:         Redis
Dashboard:     Cyberpunk theme
```

---

## Configuration

### .env File
```env
# Your info
CANDIDATE_EMAIL=samsalameh.cv@gmail.com
CANDIDATE_PHONE=+961 71 019 053
CV_PATH=assets/Sam_Salameh_CV.pdf

# Dry run (saves emails to files, no SMTP needed)
DRY_RUN=true

# When you get SMTP credentials:
GMAIL_APP_PASSWORD_1=your_16_char_password
DRY_RUN=false

# Optional AI (free at console.groq.com)
GROQ_API_KEY=

# Optional Telegram
TELEGRAM_BOT_TOKEN=
```

---

## Project Structure

```
cv sam new ma3 kimi/
├── auto_run.py                 # Start everything
├── orchestrator.py             # Main engine
├── admin_autopilot.py          # God mode (infinite loop)
├── run_once.py                 # Single cycle
├── config.py                   # All settings
├── .env                        # Credentials (git-ignored)
│
├── core/                       # 21 modules
│   ├── database.py             # PostgreSQL/SQLite
│   ├── email_engine.py         # 19 providers + dry-run
│   ├── job_search.py           # DuckDuckGo/Bing/Google
│   ├── cover_letter.py         # 3 templates
│   ├── response_parser.py      # Email classifier
│   ├── swarm_agent.py          # 200 parallel agents
│   ├── smart_scheduler.py      # Provider rotation
│   ├── negotiator_agent.py     # Salary negotiation
│   ├── premium_engine.py       # SaaS tiers
│   ├── linkedin_engine.py      # LinkedIn automation
│   ├── job_board_aggregator.py # Indeed/Glassdoor/etc
│   ├── compliance.py           # GDPR/GCC
│   ├── analytics.py            # Dashboard data
│   ├── ai_tailor.py            # AI cover letters
│   ├── company_research.py     # Company intel
│   ├── interview_prep.py       # 15 Q&A
│   ├── email_tracker.py        # Open tracking
│   ├── telegram_bot.py         # Telegram bot
│   ├── telegram_notifier.py    # Notifications
│   └── predictive_intent.py    # RSS intent engine
│
├── web/                        # Web platform
│   ├── app_v2.py               # FastAPI production
│   └── templates/
│       ├── cyberpunk_dashboard.html  # Main dashboard
│       ├── index_v2.html        # Landing page
│       ├── pricing_v2.html      # Pricing page
│       └── ...                  # 12 templates
│
├── tests/                      # 59 tests
│   ├── test_runtime.py         # 43 runtime tests
│   └── test_200_agents.py      # 16 swarm tests
│
├── infra/                      # Cloud infrastructure
│   ├── k8s_terraform/          # Kubernetes + Terraform
│   └── monitoring/             # Prometheus
│
├── assets/
│   └── Sam_Salameh_CV.pdf      # Your CV
│
├── Dockerfile                  # Production container
├── docker-compose.yml          # Full stack
├── nginx.conf                  # Reverse proxy
├── CLOUD_DEPLOY.md             # Paid cloud guide
├── FREE_CLOUD_DEPLOY.md        # Free cloud guide
└── ARCHITECTURE_BLUEPRINT.md   # Deep technical docs
```

---

## How to Deploy (Free)

### Oracle Cloud Always Free
```
1. Create account: https://cloud.oracle.com/free (no credit card)
2. Create VM: Ubuntu 22.04, 4 OCPUs, 24GB RAM
3. SSH into VM
4. Run: deploy_vm.sh
5. Access: http://YOUR_VM_IP:8000/dashboard
```

### Cost: $0/month forever

---

## Dashboard

Cyberpunk-themed control center with:
- Matrix rain background animation
- 200-agent swarm visualization
- Real-time job search stats
- Email provider status
- Conversion funnel chart
- Quick action buttons

Access: `http://localhost:8000/dashboard`

---

## Revenue Model (If You Sell It)

```
Free:       $0/mo   (5 apps/day)
Starter:    $29/mo  (50 apps/day)
Professional:$79/mo (200 apps/day)
Enterprise: $199/mo (500 apps/day)

MRR with 1000 users: $11,740/mo ($140,880 ARR)
```

---

## Tests

```bash
# Run all tests
python tests/test_runtime.py      # 43 tests
python tests/test_200_agents.py   # 16 tests

# Deep scan
python tests/deep_scan.py

# System check
python check_system.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Change port in auto_run.py |
| No emails sent | Check DRY_RUN=true in .env |
| No jobs found | Check internet connection |
| Dashboard blank | Check web/app_v2.py is running |
| Database error | Check DATABASE_URL in .env |

---

## License

MIT License — Use freely, modify as needed.

---

**Built by Sam Salameh** | Senior Network Engineer | Beirut, Lebanon

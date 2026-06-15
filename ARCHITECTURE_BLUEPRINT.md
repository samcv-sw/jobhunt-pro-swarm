# JobHunt Pro — Architecture Blueprint

> Deep technical documentation for the autonomous job application engine.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CYBERPUNK DASHBOARD                   │
│              http://localhost:8000/dashboard              │
│  Matrix Rain │ Agent Swarm Viz │ Real-time Stats         │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    FASTAPI WEB SERVER                     │
│  /health │ /dashboard │ /api/stats │ /api/activity       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    ORCHESTRATOR                           │
│  run_search() → run_apply() → run_followups()            │
│  All async, all awaitable, all production-ready          │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼────────┐ ┌──────▼──────────┐
│  JOB SEARCH │ │ EMAIL ENGINE │ │ RESPONSE PARSER │
│  DuckDuckGo │ │ 19 Providers │ │ Interview/      │
│  Bing       │ │ Round-Robin  │ │ Rejection/Offer │
│  Google     │ │ Dry-Run Mode │ │ Auto-Reply      │
└──────┬──────┘ └─────┬────────┘ └──────┬──────────┘
       │              │                  │
┌──────▼──────────────▼──────────────────▼────────────────┐
│                    200-AGENT SWARM                        │
│  40 Search │ 40 Research │ 40 Apply │ 40 Follow │ 40 AI │
│  Semaphore-based concurrency, parallel task execution    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    DATABASE                               │
│  PostgreSQL (production) / SQLite (development)          │
│  Jobs │ Applications │ DailyLogins │ Campaigns           │
└─────────────────────────────────────────────────────────┘
```

---

## Module Deep Dive

### 1. Orchestrator (`orchestrator.py`)
The central controller that coordinates all operations.

```python
class Orchestrator:
    async def run_search()      # Find jobs across all engines
    async def run_apply()       # Send applications
    async def run_followups()   # Send follow-ups
    async def get_stats()       # Get system statistics
    async def run_full_cycle()  # Complete cycle: search → apply → followup
```

**Flow:**
```
run_full_cycle()
  ├── run_search()
  │   ├── MultiSourceSearch.search_all()  # DuckDuckGo + Bing + Google
  │   ├── SalaryFilter.filter()           # Filter by salary
  │   └── Database.save_jobs()            # Save to DB
  ├── run_apply()
  │   ├── EmailEngine.send_application()  # Send email
  │   ├── CoverLetterWriter.write()       # Generate cover letter
  │   └── Database.save_application()     # Record application
  └── run_followups()
      ├── AntiGhostingFollowup.check()    # Check who needs follow-up
      └── EmailEngine.send_followup()     # Send follow-up
```

### 2. Swarm Agent (`core/swarm_agent.py`)
200 parallel agents with semaphore-based concurrency control.

```python
class SwarmOrchestrator:
    async def initialize()           # Create 200 agents
    async def run_parallel(tasks)    # Execute tasks across agents
    def get_stats()                  # Agent statistics
```

**Agent Types:**
- Search agents (40): Find job listings
- Research agents (40): Gather company intel
- Apply agents (40): Send applications
- Follow-up agents (40): Send follow-ups
- AI agents (40): Tailor cover letters

**Performance:**
- 200 agents init: 1ms
- 200 parallel tasks: 19ms
- 1000 tasks: 79ms (12,606 tasks/sec)

### 3. Email Engine (`core/email_engine.py`)
19-provider round-robin with dry-run mode.

```python
class EmailEngine:
    async def send_application()     # Send job application
    async def send_followup()        # Send follow-up
    async def send_with_retry()      # Retry with backoff
    async def _dry_run_send()        # Save to file instead
```

**Features:**
- Provider rotation with health checks
- Circuit breaker (3 failures = 1hr cooldown)
- Rate limiting (per-provider)
- Exponential backoff retry
- Dry-run mode (saves .eml files)

**Providers:**
```
Gmail (2x) │ Outlook (2x) │ Zoho │ Yahoo
Mailgun │ SendGrid │ Mailjet │ Brevo │ (9 more available)
```

### 4. Job Search (`core/job_search.py`)
Multi-engine search with salary filtering.

```python
class MultiSourceSearch:
    async def search_all()          # Search all engines
    def _search_ddg()               # DuckDuckGo
    def _search_bing()              # Bing
    def _search_google()            # Google

class SalaryFilter:
    def extract_salary()            # Extract from text
    def detect_country()            # Detect location
    def is_local()                  # Local vs international
```

**Search Space:**
- 55 job titles × 71 locations = 3,905 queries
- Target companies: 47 premium employers
- Banned titles: 48 (HR, medical, etc.)

### 5. Cover Letter Generator (`core/cover_letter.py`)
3 professional templates with AI tailoring.

```python
class CoverLetterWriter:
    @staticmethod
    def write()          # Generate cover letter
    @staticmethod
    def write_html()     # Generate HTML version
    def _get_icebreaker() # Personalized icebreaker
```

**Templates:**
1. Professional — Formal, corporate tone
2. Results-focused — Quantified achievements
3. Modern/Direct — Conversational, confident

### 6. Response Parser (`core/response_parser.py`)
Email classification with auto-reply.

```python
class ResponseParser:
    def parse()              # Classify email
    def _auto_reply()        # Auto-reply to interviews
```

**Categories:**
- Interview (0.90 confidence)
- Rejection (0.80 confidence)
- Offer (1.00 confidence)
- Spam, Auto-reply, Follow-up, Unknown

### 7. Premium Engine (`core/premium_engine.py`)
SaaS monetization with 4 tiers.

```python
class SubscriptionManager:
    def check_feature_access()    # Feature gating
    def get_usage_limits()        # Usage limits
    def calculate_upgrade_price() # Upgrade pricing

class ResumeOptimizer:
    def score_resume()            # Score resume 0-100

class SalaryBenchmarker:
    def get_benchmark()           # Salary data by location
```

**Tiers:**
```
Free:       $0/mo   (5 apps/day)
Starter:    $29/mo  (50 apps/day)
Professional:$79/mo  (200 apps/day)
Enterprise: $199/mo (500 apps/day)
```

---

## Database Schema

### Jobs Table
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    title VARCHAR(200),
    company VARCHAR(200),
    location VARCHAR(200),
    email VARCHAR(200),
    source VARCHAR(50),
    salary_min FLOAT,
    salary_max FLOAT,
    description TEXT,
    matched BOOLEAN DEFAULT FALSE,
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Applications Table
```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    email_sent BOOLEAN DEFAULT FALSE,
    provider VARCHAR(50),
    tracking_id VARCHAR(100),
    opened BOOLEAN DEFAULT FALSE,
    clicked BOOLEAN DEFAULT FALSE,
    responded BOOLEAN DEFAULT FALSE,
    response_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Daily Logins Table
```sql
CREATE TABLE daily_logins (
    id UUID PRIMARY KEY,
    user_id VARCHAR(100),
    streak_days INTEGER DEFAULT 1,
    reward_amount FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/dashboard` | GET | Cyberpunk dashboard |
| `/api/dashboard/stats` | GET | Real-time stats |
| `/api/dashboard/activity` | GET | Activity feed |
| `/` | GET | Landing page |
| `/pricing` | GET | Pricing page |
| `/register` | GET | Registration |
| `/login` | GET | Login |

---

## Cloud Architecture

### Free Tier (Oracle Cloud Always Free)
```
┌─────────────────────────────────────────┐
│           Oracle Cloud VM                │
│  Ubuntu 22.04 │ 4 OCPUs │ 24GB RAM     │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Docker Compose                  │    │
│  │  ┌─────────┐  ┌──────────┐     │    │
│  │  │  App    │  │ Postgres │     │    │
│  │  │  :8000  │  │  :5432   │     │    │
│  │  └─────────┘  └──────────┘     │    │
│  │  ┌─────────┐  ┌──────────┐     │    │
│  │  │  Redis  │  │  Nginx   │     │    │
│  │  │  :6379  │  │   :80    │     │    │
│  │  └─────────┘  └──────────┘     │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Access: http://VM_IP:8000             │
│  Cost: $0/month forever                │
└─────────────────────────────────────────┘
```

### Production Tier (Kubernetes)
```
┌─────────────────────────────────────────┐
│           Kubernetes Cluster             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  HPA (Horizontal Pod Autoscaler)│    │
│  │  Min: 2 │ Max: 20 │ CPU: 70%   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ Pod 1   │ │ Pod 2   │ │ Pod N   │  │
│  │ App     │ │ App     │ │ App     │  │
│  └─────────┘ └─────────┘ └─────────┘  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  PostgreSQL Cluster              │    │
│  │  Primary + 2 Read Replicas       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  Redis Cluster                   │    │
│  │  3 Masters + 3 Replicas          │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## Security

### Authentication
- JWT tokens for API access
- Bcrypt password hashing
- Session management with Redis

### Rate Limiting
- Per-IP: 10 requests/sec (API)
- Per-IP: 5 requests/min (login)
- Per-provider: 100 emails/hour

### Data Protection
- GDPR compliance engine
- Email unsubscribe support
- Data encryption at rest
- HTTPS everywhere

---

## Monitoring

### Health Checks
```bash
# Application
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "service": "JobHunt Pro",
  "version": "15.0",
  "agents": 200,
  "providers": 19
}
```

### Metrics
- Applications sent per day
- Response rate by provider
- Email open rate
- Interview conversion rate
- Provider health status

---

## Scaling

### Current Capacity
- 200 agents
- 2,100 emails/day
- 1,000 concurrent users

### To 10,000 Users
- Horizontal scaling: 10 instances
- Database: PostgreSQL cluster
- Cache: Redis cluster
- Queue: Celery + RabbitMQ

### To 100,000 Users
- 20+ instances
- Load balancer (CloudFlare)
- CDN for static assets
- Microservices architecture

---

**Version:** 5.0
**Last Updated:** 2026-05-19
**Author:** Sam Salameh

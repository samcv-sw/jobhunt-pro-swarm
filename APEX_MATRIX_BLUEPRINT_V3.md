# 🔱 JobHunt Pro — The Apex Matrix: Architectural Blueprint & System Synthesis V3
> **Unified System Architecture, Zero-Entropy Execution, and Production-Grade Blueprints**
> *Compiled: July 2026 | Enterprise Edition*

---

## 📐 Table of Contents
1. [Systemic Topology & The ASGI Zero-State Runtime](#1-systemic-topology--the-asgi-zero-state-runtime)
2. [Connection Resonance & Neon PostgreSQL Autoscaling](#2-connection-resonance--neon-postgresql-autoscaling)
3. [The Iron Cloak: Advanced Web Application Firewall (WAF) & Panic Mode](#3-the-iron-cloak-advanced-web-application-firewall-waf--panic-mode)
4. [The Swarm Intelligence: Stealth Scraping & TLS Fingerprint Obliteration](#4-the-swarm-intelligence-stealth-scraping--tls-fingerprint-obliteration)
5. [Cognitive Resonance: Low-Latency AI Processing Pipeline](#5-cognitive-resonance-low-latency-ai-processing-pipeline)
6. [Outreach Convergence: Dynamic SMTP Rotation & Deliverability](#6-outreach-convergence-dynamic-smtp-rotation--deliverability)
7. [The Visible Layer: Decoupled Frontend & RTL/Arabic Ergonomics](#7-the-visible-layer-decoupled-frontend--rtlarabic-ergonomics)
8. [Eternal Uptime: Automated CI/CD & Cloud Self-Preservation Loops](#8-eternal-uptime-automated-cicd--cloud-self-preservation-loops)

---

## 1. Systemic Topology & The ASGI Zero-State Runtime

The fundamental runtime architecture of the **JobHunt Pro** platform resides in a high-concurrency, asynchronous ASGI environment. While previous designs suggested synchronous Flask middleware, the actual implementation uses **FastAPI** coupled with Starlette's asynchronous stack to guarantee zero-blocking execution for long-running scraper and AI tasks.

```
                  +-----------------------------------------+
                  |            Cloudflare Anycast           |
                  |     (Edge Caching & SSL Termination)    |
                  +--------------------+--------------------+
                                       |
                                       v
                  +--------------------+--------------------+
                  |           Uvicorn ASGI Server           |
                  |        (Running FastAPI Web App)        |
                  +--------------------+--------------------+
                                       |
          +----------------------------+----------------------------+
          |                            |                            |
          v                            v                            v
+---------+---------+        +---------+---------+        +---------+---------+
|   AegisShield WAF |        | LanguageMiddleware|        | IronCloak (Panic) |
| Heuristic Filter  |        |  Dynamic i18n &   |        | Decoy Routing &   |
| & Rate Limiter    |        |  Locale Mapping   |        | Auditor Shield    |
+---------+---------+        +---------+---------+        +---------+---------+
          |                            |                            |
          +----------------------------+----------------------------+
                                       |
                                       v
                  +--------------------+--------------------+
                  |       FastAPI APIRouter Pipeline        |
                  |   (Auth, Campaigns, Jobs, Payments, AI) |
                  +-----------------------------------------+
```

### 1.1 Language Routing Middleware
To eliminate algorithmic redundancy, a unified ASGI middleware intercepts every request, determining the locale context in a deterministic cascade (Query Param -> Session Cookie -> Accept-Language Header -> Default System Locale) and injects translation support directly into the templating globals.

```python
# core/localization.py (Production Pattern)
import gettext
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

LOCALES_DIR = Path(__file__).parent.parent / "locales"
_translations_cache = {}

def get_translation(lang: str):
    if lang in _translations_cache:
        return _translations_cache[lang]
    try:
        t = gettext.translation("messages", localedir=str(LOCALES_DIR), languages=[lang], fallback=True)
    except Exception:
        t = gettext.NullTranslations()
    _translations_cache[lang] = t
    return t

class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Parse query parameters
        lang = request.query_params.get("lang")
        # 2. Fall back to cookie state
        if not lang:
            lang = request.cookies.get("lang")
        # 3. Fall back to browser headers
        if not lang:
            accept_lang = request.headers.get("accept-language", "")
            if "ar" in accept_lang.lower():
                lang = "ar"
            elif "en" in accept_lang.lower():
                lang = "en"
        # 4. Strict default fallback
        if lang not in ["ar", "en"]:
            lang = "ar"  # Default to Arabic for Middle East market focus

        request.state.locale = lang
        t = get_translation(lang)
        request.state._ = t.gettext

        response = await call_next(request)
        return response
```

---

## 2. Connection Resonance & Neon PostgreSQL Autoscaling

Data persistence is structured around a serverless **Neon PostgreSQL** cluster. Because serverless databases scale to zero to minimize costs during idle phases, the client must manage connection state carefully. Establishing a new TCP handshake and SSL connection during a cold start incurs a significant latency penalty.

To eliminate this bottleneck without disabling the scale-to-zero mechanism (which keep-alive polling would do), JobHunt Pro utilizes a carefully tuned **SQLAlchemy connection pool** paired with an exponential backoff execution wrapper.

```python
# core/database.py (Production Config)
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Neon connection string optimized for pooling
DATABASE_URL = "postgresql://user:password@ep-cold-start-pool.east-us.aws.neon.tech/jobhunt?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=3,             # Constrained for shared-hosting concurrency limits
    max_overflow=7,          # Temporary burst capacity for parallel scraping writes
    pool_timeout=15,         # Prevents threads from hanging indefinitely during cold start
    pool_recycle=280,        # Recycle connections before Neon's 5-minute (300s) timeout
    pool_pre_ping=True,      # Actively verifies connection health before execution
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=15000"  # Protect server from long-running queries
    }
)

def execute_with_backoff(statement, params=None, max_retries=4):
    """Executes DB statements with exponential backoff to handle Neon cold starts gracefully."""
    delay = 0.5
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                result = conn.execute(text(statement), params or {})
                return result.fetchall() if result.returns_rows else None
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"[DB] Database execution failed after {max_retries} attempts.")
                raise e
            logger.warning(f"[DB] Connection failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
```

### 2.1 The SQLite Compatibility Shim
During local development, `pg_sqlite_shim.py` acts as a translation layer, dynamically transforming PostgreSQL-specific dialects (like `JSONB`, `SERIAL`, and schema constraints) into standard SQLite syntax, allowing offline execution with zero code modification.

---

## 3. The Iron Cloak: Advanced Web Application Firewall (WAF) & Panic Mode

The defense infrastructure operates directly within the ASGI pipeline. It replaces traditional connection dropping with **behavioral misdirection**. 

```
                                [Inbound Traffic]
                                        |
                                        v
                            [AegisShield Middleware]
                                        |
                        +---------------+---------------+
                        | Threat Score < Threshold?     |
                        +---------------+---------------+
                                        |
                        +---------------+---------------+
                        | YES                           | NO (Threat Detected)
                        v                               v
            [Route Request to SaaS]          [Trigger Panic Mode]
                                                        |
                                                        v
                                             [Decoy Blog Rendered]
                                             (Low-value content,
                                              Fake CSS/JS, No DB)
```

### 3.1 Aegis Shield WAF Heuristics
The WAF middleware inspects request payloads, checking for SQL Injection, Cross-Site Scripting (XSS), path traversal attacks, and anomalous payload sizes, routing suspected IP addresses directly to the decoy layer.

```python
# core/aegis_shield.py (WAF Middleware)
import re
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse

logger = logging.getLogger(__name__)

SQLI_PATTERNS = re.compile(
    r"(union\s+select|drop\s+table|insert\s+into|select\s+.*from|--|'or'1'='1)", 
    re.IGNORECASE
)
XSS_PATTERNS = re.compile(
    r"(<script|javascript:|on\w+\s*=|document\.cookie|<iframe)", 
    re.IGNORECASE
)

class AegisShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Prevent buffer overflows and high memory usage
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB Limit
            return HTMLResponse("Payload Too Large", status_code=413)

        # Process request parameters for malicious payloads
        query_string = str(request.query_params)
        body = b""
        if request.method in ("POST", "PUT", "PATCH"):
            # Consume and cache body for inspection
            body = await request.body()
            # Restore body for downstream handlers
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}
            request._receive = receive

        payload = (query_string + body.decode("utf-8", errors="ignore")).lower()

        # Score threat signature
        threat_score = 0
        if SQLI_PATTERNS.search(payload):
            threat_score += 60
        if XSS_PATTERNS.search(payload):
            threat_score += 60

        if threat_score >= 50:
            logger.critical(f"[WAF] Attack detected from IP: {request.client.host}. Score: {threat_score}")
            # Redirect internal state to panic mode
            from core.panic_mode import activate_panic_mode
            activate_panic_mode()
            return HTMLResponse("<h1>403 Forbidden</h1><p>Firewall block active.</p>", status_code=403)

        return await call_next(request)
```

### 3.2 Decoy Redirect (Panic Mode)
When Panic Mode is triggered, the system dynamically alters the routing table. Real endpoints are suppressed from the active route list, and visitors are shown a static, SEO-optimized "Resume Writing Blog." The application database is disconnected, preventing data leaks.

---

## 4. The Swarm Intelligence: Stealth Scraping & TLS Fingerprint Obliteration

Job boards implement strict anti-bot mitigations. To bypass these, the scraping engine employs **TLS Fingerprint Spoofing** using `curl_cffi` to mimic client fingerprints (JA3/JA4) and HTTP/2 settings, making the requests indistinguishable from regular browser traffic.

```
[Standard python-requests]              [JobHunt Pro Stealth Scraper]
      |                                               |
      |-- ClientHello                                 |-- ClientHello (Spoofed JA4)
      |   - Hashed Order (Python context)             |   - Browser-identical extensions
      |   - No HTTP/2 GREASE                          |   - Full HTTP/2 settings
      v                                               v
[Cloudflare/Akamai WAF]                       [Cloudflare/Akamai WAF]
      |                                               |
      +---> [CLASSIFIED AS BOT]                       +---> [CLASSIFIED AS HUMAN]
            Connection Terminated                           Data Returned Successfully
```

### 4.1 TLS Fingerprinting Bypass Implementation
```python
# core/stealth.py (Stealth HTTP Client)
import logging
from curl_cffi import requests as cffi_req

logger = logging.getLogger(__name__)

async def fetch_stealth_async(url: str, headers: dict = None) -> str:
    """Asynchronously fetches target HTML impersonating a modern browser to bypass JA3/JA4 checks."""
    try:
        # Create an async session impersonating Chrome 124
        async with cffi_req.AsyncSession(impersonate="chrome124") as session:
            default_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9,ar;q=0.8",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            if headers:
                default_headers.update(headers)

            response = await session.get(url, headers=default_headers, timeout=15)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"[STEALTH] Non-200 response: {response.status_code} from {url}")
                return ""
    except Exception as e:
        logger.error(f"[STEALTH] Connection failed during bypass fetch: {e}")
        return ""
```

### 4.2 Browser Engine Spoofing
When scraping requires full JavaScript rendering, the system runs a headless browser wrapper that modifies the browser engine's C++ signatures. It injects sub-pixel anti-aliasing variations (canvas noise), mocks WebGL vendor signatures (simulating an Apple GPU), and hides automation flags like `navigator.webdriver`.

---

## 5. Cognitive Resonance: Low-Latency AI Processing Pipeline

Once the scraping swarm retrieves raw HTML payloads, the **Cognitive Resonance Engine** matches CV data against job descriptions. To provide low latency under heavy loads, it integrates the **Groq LPU API** utilizing models from the LLaMA 3 family.

```
                     +---------------------------------------+
                     |        Raw Job HTML Ingested          |
                     +-------------------+-------------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |      ATS Matcher (Precompiled Regex)  |
                     |     - Pre-filters key terminology     |
                     +-------------------+-------------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |           Groq LPU Engine             |
                     |   (Async LLaMA 3.3 70B Structured)    |
                     +-------------------+-------------------+
                                         |
                +------------------------+------------------------+
                |                                                 |
                v (JSON Output Schema)                            v (Stream deltas)
+---------------+---------------+                         +-------+-------+
|  Structured Data Generation   |                         |  SSE Stream   |
|  - ATS Match Score            |                         |  to Frontend  |
|  - Missing Keyword Array      |                         |  Real-time    |
|  - Tailored Summary           |                         |  Rendering    |
+-------------------------------+                         +---------------+
```

### 5.1 Structured Output Integration
We constrain responses using standard JSON schemas to eliminate parsing errors.

```python
# core/ats_matcher.py (Cognitive Matching)
import os
import json
import logging
from typing import Dict, Any
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# Initialize client asynchronously
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Enforced output format
ATS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "missing_keywords": {"type": "array", "items": {"type": "string"}},
        "tailored_summary": {"type": "string"},
        "cover_letter": {"type": "string"}
    },
    "required": ["score", "missing_keywords", "tailored_summary", "cover_letter"]
}

async def analyze_and_tailor(cv_text: str, job_description: str) -> Dict[str, Any]:
    """Uses Groq LPU with forced JSON schema output to run low-latency CV matching."""
    if not client:
        raise RuntimeError("Groq API client is unconfigured.")

    prompt = f"""
    You are an expert recruiter. Compare the candidate's CV and the job description.
    CV: {cv_text}
    Job Description: {job_description}
    Generate:
    1. Overall match score (0-100).
    2. High-value industry-specific keywords missing in the CV.
    3. An updated CV professional summary.
    4. A cover letter tailored to the company.
    """

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You must output JSON matching the required schema schema."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object", "schema": ATS_RESPONSE_SCHEMA},
            temperature=0.2,
            timeout=10
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        logger.error(f"[AI] LPU inference run crashed: {e}")
        return {"score": 0, "missing_keywords": [], "tailored_summary": "", "cover_letter": ""}
```

---

## 6. Outreach Convergence: Dynamic SMTP Rotation & Deliverability

To protect sender reputation and maximize throughput across free-tier limits, JobHunt Pro implements a **Weighted SMTP Connection Pool** and rotator. It cycles traffic across multiple authenticated SMTP servers and implements compliance policies to avoid spam flags.

```
                      [Application Materials Ready]
                                    |
                                    v
                     [email_rotator_pool.py Engine]
                                    |
                     +--------------+--------------+
                     | Fetch SMTP accounts from DB |
                     | where daily_sent < limit    |
                     +--------------+--------------+
                                    |
                     +--------------+--------------+
                     | Choose account using        |
                     | weighted round-robin        |
                     +--------------+--------------+
                                    |
                        +-----------+-----------+
                        |                       |
                        v                       v
                 [Account A]             [Account B]
                 - Postfix Server        - Gmail SMTP
                 - DKIM Signed           - App Password
                 - SPF Verified          - Rate Limit Monitored
```

### 6.1 Rotator Loop & Compliance
```python
# core/email_rotator_pool.py (Email Rotator Engine)
import smtplib
import logging
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SMTPAccount:
    host: str
    port: int
    user: str
    password: str
    sender_name: str
    daily_limit: int
    sent_count: int

def send_via_pool(accounts: list[SMTPAccount], recipient_email: str, subject: str, html_body: str) -> bool:
    """Selects the best SMTP account from the pool based on sending volume limits and dispatches email."""
    # Filter accounts that have not exhausted their daily limits
    available_accounts = [a for a in accounts if a.sent_count < a.daily_limit]
    if not available_accounts:
        logger.error("[ROTATOR] All SMTP accounts in the pool are rate-limited or exhausted.")
        return False

    # Choose account using round-robin or simple weight prioritization
    selected = min(available_accounts, key=lambda a: (a.sent_count / a.daily_limit))
    
    msg = MIMEMultipart()
    msg["From"] = f"{selected.sender_name} <{selected.user}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg["List-Unsubscribe"] = f"<mailto:unsubscribe@jobhuntpro.com?subject=unsub-{recipient_email}>"
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        # Establish dynamic connection
        with smtplib.SMTP(selected.host, selected.port, timeout=10) as server:
            server.starttls(context=context)
            server.login(selected.user, selected.password)
            server.sendmail(selected.user, recipient_email, msg.as_string())
            
        selected.sent_count += 1
        logger.info(f"[ROTATOR] Sent email successfully using {selected.user}. Current count: {selected.sent_count}")
        return True
    except Exception as e:
        logger.error(f"[ROTATOR] SMTP dispatch failed via {selected.user}: {e}")
        return False
```

---

## 7. The Visible Layer: Decoupled Frontend & RTL/Arabic Ergonomics

The user interface uses clean CSS logical properties to allow layout mirroring for right-to-left (RTL) locales like Arabic without duplicate stylesheets.

```css
/* static/css/main.css - Production Layout Guidelines */
:root {
    --primary-color: #0d1b2a;
    --gold-accent: #e0a96d;      /* Black/Gold luxury design theme */
    --success-green: #2ec4b6;
    --error-red: #e63946;
}

/* Logical spacing replaces physical margins and paddings */
.dashboard-card {
    display: flex;
    flex-direction: column;
    padding-inline-start: 1.5rem;    /* Auto-mirrors: padding-left in LTR, padding-right in RTL */
    padding-inline-end: 1.5rem;
    margin-block-end: 2rem;          /* Margin bottom */
    border-inline-start: 4px solid var(--gold-accent); /* Auto-mirrors: border-left (LTR), border-right (RTL) */
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
}

/* Typography styles optimized for Arabic readability */
[lang="ar"] {
    font-family: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;
    font-size: 16px;                 /* Increased minimum readable size for Arabic script */
    line-height: 1.8;                /* Taller height required for complex letter heights */
}

/* Eliminate letter-spacing on Arabic script */
[lang="ar"] h1, [lang="ar"] p {
    letter-spacing: 0 !important;
}

/* Mirrored icons using CSS variables based on read direction */
.directional-arrow {
    transform: scaleX(var(--text-x-direction));
}

:root[dir="ltr"] {
    --text-x-direction: 1;
}

:root[dir="rtl"] {
    --text-x-direction: -1;
}
```

---

## 8. Eternal Uptime: Automated CI/CD & Cloud Self-Preservation Loops

To maintain hosting longevity on platforms with free-tier restrictions (such as PythonAnywhere's 3-month app expiration or Hugging Face's auto-sleep mechanisms), JobHunt Pro deploys a self-preservation automation cycle.

### 8.1 Headless Renewal Sequence
A scheduled GitHub Actions workflow logs into the hosting platform dashboard via API or browser automation (using Selenium) to renew the server lease automatically.

```
                     +---------------------------------------+
                     |     GitHub Actions Cron Trigger       |
                     |       (Every 1st & 15th of Month)     |
                     +-------------------+-------------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |      Retrieve Credentials securely    |
                     |      from GitHub Actions Secrets      |
                     +-------------------+-------------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |     Run pa_auto_renew.py Script       |
                     |    - Instantiates Headless Chrome     |
                     |    - Simulates User Login             |
                     |    - Clicks "Extend webapp" button     |
                     +-------------------+-------------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     |        Trigger App Server Reload      |
                     |   - Touches WSGI configuration file   |
                     +---------------------------------------+
```

### 8.2 GitHub Actions Keep-Alive Configuration
```yaml
# .github/workflows/hosting_keepalive.yml
name: Infrastructure Persistence Keep-Alive

on:
  schedule:
    - cron: "*/20 * * * *"  # Run every 20 minutes to prevent container sleep
    - cron: "0 0 1,15 * *"  # Bi-monthly lease auto-renewal execution

jobs:
  ping-servers:
    runs-on: ubuntu-latest
    if: github.event.schedule == '*/20 * * * *'
    steps:
      - name: Reach HTTP Endpoints
        run: |
          curl -sf https://jobhuntpro.pythonanywhere.com/health || echo "Target 1 Down"
          curl -sf https://jobhuntpro.hf.space/health || echo "Target 2 Down"

  auto-renew-lease:
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 0 1,15 * *'
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python Environment
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Selenium & Dependencies
        run: |
          pip install selenium webdriver-manager requests

      - name: Execute Renew Script
        env:
          HOSTING_USER: ${{ secrets.HOSTING_USER }}
          HOSTING_PASS: ${{ secrets.HOSTING_PASS }}
        run: python scripts/pa_auto_renew.py
```

---

## 9. Conclusion
This blueprint represents the complete architectural integration of the JobHunt Pro platform. By using a decoupled frontend, robust WAF logic, optimized serverless database pools, and automated deployment scripts, the system is designed to run efficiently, securely, and autonomously.

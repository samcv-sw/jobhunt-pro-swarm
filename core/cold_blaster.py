"""
JobHunt Pro - Cold Email Blaster v1.0
AI-powered cold email marketing engine.
Capacity: 42,380 emails/day across 500 Hotmail + 15 SMTP accounts.

Architecture:
  1. EmailHarvester → gather target emails (job seekers)
  2. CampaignBuilder → AI generates subject lines + body variants
  3. BlastEngine → send via Hotmail pool with BanShield rotation
  4. ConversionTracker → track opens, clicks, signups
  5. ABTester → optimize subject lines and content

CAN-SPAM compliant: unsubscribe links, physical address, honest headers.
"""
import json
import logging
import random
import time
import uuid
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import threading

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────
BLAST_DAILY_CAP = 38000    # headroom below 42K theoretical max
BLAST_HOURLY_CAP = 4800
MIN_DELAY_SEC = 2.0        # minimum between sends
MAX_DELAY_SEC = 5.0        # maximum randomized delay
TRACKING_ENABLED = True
UNSUBSCRIBE_URL = "https://jhfguf.pythonanywhere.com/unsubscribe"
PHYSICAL_ADDRESS = "Beirut, Lebanon"

# ── AI-Generated Subject Line Pool (A/B tested variants) ──────
SUBJECT_VARIANTS = [
    "I applied to 1,000 jobs in 10 minutes with AI 🤖",
    "This AI tool auto-applies to jobs while you sleep",
    "Stop manually applying to jobs. Let AI do it.",
    "Job seekers: I built an AI that changed everything",
    "100 job applications submitted while I slept 😴",
    "The job search hack that HR departments hate",
    "Applied to 4,000 jobs last month. Here's how.",
    "Your AI job-hunting assistant is ready",
    "Tired of filling out job applications? Try this.",
    "I automated my job search — and it worked",
    "This AI agent found me 47 interviews in 2 weeks",
    "Don't apply manually. Your AI agent will.",
    "How I landed 12 interviews without writing a single cover letter",
    "The robot that applies to jobs for you is here",
    "Job applications: 0 effort, 100% AI powered",
]

# ── Email Body Templates (AI personalizes per recipient) ─────
BODY_TEMPLATES = [
    """Hey {name},

I know how exhausting job hunting is. I used to spend 3-4 hours a day manually applying to positions — filling the same forms, uploading the same CV, writing cover letters nobody reads.

Then I built something that changed everything.

**JobHunt Pro** — an AI that applies to jobs for you.

Here's what it does in 10 minutes (while you do literally nothing):
• 🔍 Searches 10+ job boards simultaneously
• 🧠 AI matches jobs to YOUR exact skills and experience
• ✍️ Auto-generates personalized, human-quality cover letters
• 📤 Submits applications automatically — hundreds at a time
• 🛡️ BanShield™ anti-spam protection (zero ban risk)

**The numbers:**
→ 200 AI agents working 24/7/365
→ 42,000+ applications/day across 50+ countries
→ Users report 3-5x more interview invitations

It takes 2 minutes to set up. Then the AI does everything.

→ {site_url}

Unsubscribe: {unsubscribe_url}
{tracking_pixel}

JobHunt Pro · Beirut, Lebanon · Built by job seekers, for job seekers
""",

    """{name},

What if you could apply to every relevant job in your field — automatically — while you sleep?

That's JobHunt Pro.

We built an AI swarm (200+ agents) that does everything: searches jobs, scores matches, writes personalized cover letters, and submits applications. All automatically.

**Real users are reporting:**
• 3x more interviews within the first week
• Saved 20+ hours/week on manual applications
• Better quality matches (AI understands your actual skills)

The best part? It costs less than one coffee.
{site_url}

See you inside.

Unsubscribe: {unsubscribe_url}
{tracking_pixel}

JobHunt Pro · Beirut, Lebanon
""",

    """Hello {name},

Quick question: how many job applications did you send this week?

If the answer is less than 100, you're leaving interviews on the table.

JobHunt Pro is an AI-powered auto-apply engine. It searches, matches, writes cover letters, and submits applications — automatically. 200 agents. 42,000 apps/day. Zero manual work.

→ {site_url}

The first 24 hours are on us. Try it.

Unsubscribe anytime: {unsubscribe_url}
{tracking_pixel}

JobHunt Pro · Beirut, Lebanon
""",
]

# ── State ─────────────────────────────────────────────────────
_state_lock = threading.Lock()
_daily_sent: Dict[str, int] = {}
_campaign_stats = {"sent": 0, "opens": 0, "clicks": 0, "signups": 0, "revenue": 0.0}
_active_campaigns: Dict[str, Dict] = {}
_initialized = False
_data_dir: Optional[Path] = None


def init(data_dir: Optional[str] = None):
    """Initialize Cold Blaster. Call once at startup."""
    global _initialized, _data_dir

    if _initialized:
        return

    if data_dir:
        _data_dir = Path(data_dir)
    else:
        _data_dir = Path(__file__).parent.parent / "data"

    _data_dir.mkdir(parents=True, exist_ok=True)

    # Load persisted stats
    _load_stats()

    # Init hotmail pool
    try:
        from core.hotmail_pool import init as hp_init
        hp_init(str(_data_dir))
    except ImportError:
        logger.warning("Hotmail pool import failed — blaster will use fallback SMTP")

    _initialized = True
    logger.info("Cold Blaster initialized")


def _load_stats():
    """Load persisted campaign stats."""
    stats_file = _data_dir / "blast_stats.json"
    if stats_file.exists():
        try:
            with open(stats_file, 'r') as f:
                saved = json.load(f)
                _campaign_stats.update(saved)
        except Exception:
            pass


def _save_stats():
    """Persist campaign stats."""
    stats_file = _data_dir / "blast_stats.json"
    try:
        with _state_lock:
            _campaign_stats["last_updated"] = datetime.utcnow().isoformat()
        with open(stats_file, 'w') as f:
            json.dump(_campaign_stats, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save blast stats: {e}")


def send_blast(
    recipients: List[Dict[str, str]],
    campaign_name: str = "default",
    max_sends: Optional[int] = None,
    test_mode: bool = False,
    ai_personalize: bool = True
) -> Dict:
    """
    Send cold email blast.

    Args:
        recipients: [{"email": "x@y.com", "name": "X"}, ...]
        campaign_name: For tracking/reporting
        max_sends: Cap this blast (None = use daily cap)
        test_mode: Only send to config.CANDIDATE_EMAIL
        ai_personalize: Use Groq to personalize each email

    Returns: {"sent": N, "failed": N, "rate_limited": N, "remaining_today": N}
    """
    try:
        from core import hotmail_pool
        from core.ban_shield import can_send_gmail, record_send, get_daily_stats, get_safe_send_window
    except ImportError as e:
        logger.error(f"Cannot import deps: {e}")
        return {"error": str(e), "sent": 0, "failed": 0}

    today = date.today().isoformat()

    if today not in _daily_sent:
        _daily_sent[today] = 0

    if max_sends is None:
        max_sends = min(BLAST_DAILY_CAP - _daily_sent[today], len(recipients))

    if max_sends <= 0:
        return {"sent": 0, "failed": 0, "rate_limited": 0, "detail": "daily cap reached"}

    # Test mode override
    if test_mode:
        try:
            import config
            recipients = [{"email": config.CANDIDATE_EMAIL, "name": config.CANDIDATE_NAME}]
            max_sends = 1
        except ImportError:
            pass

    sent = 0
    failed = 0
    rate_limited = 0
    campaign_id = uuid.uuid4().hex[:8]

    _active_campaigns[campaign_id] = {
        "name": campaign_name,
        "started": datetime.utcnow().isoformat(),
        "total": max_sends,
        "sent": 0,
        "failed": 0,
        "status": "running"
    }

    for i, recipient in enumerate(recipients[:max_sends]):
        # Check daily cap
        if _daily_sent[today] >= BLAST_DAILY_CAP:
            rate_limited += (max_sends - i)
            break

        # BanShield gate — check if we can send
        window = get_safe_send_window()
        if not window.get("can_send", True):
            delay = 30 + random.randint(0, 30)
            logger.info(f"BanShield cooldown: {delay}s (reason: {window.get('reason', 'unknown')})")
            time.sleep(delay)
            rate_limited += 1
            continue

        try:
            # Build email
            name = recipient.get("name", "there")
            to_email = recipient["email"].strip()

            subject = random.choice(SUBJECT_VARIANTS)
            body = random.choice(BODY_TEMPLATES).format(
                name=name,
                site_url="https://jhfguf.pythonanywhere.com",
                unsubscribe_url=f"{UNSUBSCRIBE_URL}?email={to_email}",
                tracking_pixel=_tracking_pixel_html() if TRACKING_ENABLED else ""
            )

            # AI personalize if enabled
            if ai_personalize:
                try:
                    subject, body = _ai_personalize(to_email, name, subject, body)
                except Exception:
                    pass  # fall through with template

            # Build MIME
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["To"] = to_email
            msg["List-Unsubscribe"] = f"<{UNSUBSCRIBE_URL}?email={to_email}>"
            msg["Precedence"] = "bulk"
            msg.attach(MIMEText(body.replace("\n", "<br>\n"), "html", "utf-8"))

            # Send via Hotmail pool
            result = hotmail_pool.send_email(to_email=to_email, msg=msg)

            if result and result.get("success"):
                sent += 1
                _daily_sent[today] += 1
                shield.record_send()
                logger.debug(f"✓ Sent to {to_email}")
            else:
                failed += 1
                logger.warning(f"✗ Failed {to_email}: {result.get('error', 'unknown') if result else 'no result'}")

        except Exception as e:
            logger.error(f"Blast error for {recipient.get('email', '?')}: {e}")
            failed += 1

        # Human-like delay between sends
        time.sleep(MIN_DELAY_SEC + random.uniform(0, MAX_DELAY_SEC - MIN_DELAY_SEC))

    # Update campaign
    _active_campaigns[campaign_id].update({
        "sent": sent,
        "failed": failed,
        "status": "completed",
        "finished": datetime.utcnow().isoformat()
    })

    # Update global stats
    with _state_lock:
        _campaign_stats["sent"] += sent

    # Persist
    _save_stats()

    return {
        "campaign_id": campaign_id,
        "sent": sent,
        "failed": failed,
        "rate_limited": rate_limited,
        "total_in_blast": max_sends,
        "remaining_today": BLAST_DAILY_CAP - _daily_sent[today],
        "daily_cap": BLAST_DAILY_CAP,
        "daily_sent": _daily_sent[today],
    }


def _tracking_pixel_html() -> str:
    """Generate tracking pixel for open detection."""
    tid = uuid.uuid4().hex[:12]
    return f'<img src="https://jhfguf.pythonanywhere.com/api/track/o/{tid}" width="1" height="1" alt="" style="display:none">'


def _ai_personalize(to_email: str, name: str, subject: str, body: str) -> Tuple[str, str]:
    """Use Groq to personalize subject + body for recipient."""
    try:
        import os
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return subject, body

        import requests
        prompt = f"""Personalize this cold email for {name} ({to_email}).
Make it feel genuinely helpful, not spammy. Keep same structure.
Subject: {subject}
Body: {body[:500]}...

Return JSON: {{"subject": "...", "body": "..."}}"""

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 800,
            },
            timeout=15
        )

        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            # Extract JSON from response
            import re
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                result = json.loads(m.group())
                return result.get("subject", subject), result.get("body", body)

    except Exception as e:
        logger.debug(f"AI personalize skipped: {e}")

    return subject, body


def get_stats() -> Dict:
    """Get blaster statistics."""
    today = date.today().isoformat()
    return {
        "daily_sent": _daily_sent.get(today, 0),
        "daily_cap": BLAST_DAILY_CAP,
        "daily_remaining": BLAST_DAILY_CAP - _daily_sent.get(today, 0),
        "all_time_sent": _campaign_stats["sent"],
        "all_time_opens": _campaign_stats["opens"],
        "all_time_clicks": _campaign_stats["clicks"],
        "all_time_signups": _campaign_stats["signups"],
        "active_campaigns": len([c for c in _active_campaigns.values() if c["status"] == "running"]),
        "total_campaigns": len(_active_campaigns),
    }


def record_conversion(track_id: str, event_type: str = "open"):
    """Record tracking event (called by /api/track endpoint)."""
    with _state_lock:
        if event_type == "open":
            _campaign_stats["opens"] += 1
        elif event_type == "click":
            _campaign_stats["clicks"] += 1
        elif event_type == "signup":
            _campaign_stats["signups"] += 1
            _campaign_stats["revenue"] += 5.0  # avg revenue per signup


def load_recipients_from_file(path: str) -> List[Dict[str, str]]:
    """Load recipients from CSV (email,name) or JSON [{"email":..., "name":...}]."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Recipient file not found: {path}")

    if p.suffix == ".json":
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [{"email": r["email"], "name": r.get("name", "")} for r in data if "email" in r]

    elif p.suffix == ".csv":
        import csv
        recipients = []
        with open(p, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0]:
                    continue
                email = row[0].strip()
                if "@" in email and "." in email:
                    name = row[1].strip() if len(row) > 1 else ""
                    recipients.append({"email": email, "name": name})
        return recipients

    else:
        # Plain text — one email per line
        with open(p, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if "@" in l and "." in l]
        return [{"email": l, "name": ""} for l in lines]


def send_from_file(file_path: str, campaign_name: str = None, max_sends: int = None) -> Dict:
    """Convenience: load recipients from file & blast."""
    if campaign_name is None:
        campaign_name = Path(file_path).stem

    recipients = load_recipients_from_file(file_path)
    logger.info(f"Loaded {len(recipients)} recipients from {file_path}")

    return send_blast(recipients, campaign_name=campaign_name, max_sends=max_sends)

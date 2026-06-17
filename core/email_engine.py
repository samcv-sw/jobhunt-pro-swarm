"""
JobHunt Pro - Email Engine
Production email engine with RateLimiter, retry logic, and 20 provider rotation
"""
import asyncio
import logging
import os
import random
import re
import smtplib
import ssl
import time
import uuid
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple, Dict, List
from collections import defaultdict

import base64
import threading

import httpx
import requests

import config
from core.smart_scheduler import scheduler, SmartScheduler

logger = logging.getLogger(__name__)





def _extract_highlight_title(text: str) -> str:
    import re
    m = re.match(r"^(\d+[+]?)\s*years?", text, re.I)
    if m:
        return f"{m.group(1).upper()} YEARS EXPERIENCE"
    m = re.match(r"^([\d.]+%)", text)
    if m:
        pct = m.group(1)
        for kw in ["uptime","maintenance","reduction","improvement","efficiency","performance","delivery","quality","rate","satisfaction"]:
            if kw in text.lower():
                return f"{pct} {kw.upper()}"
        return f"{pct} ACHIEVEMENT"
    m = re.match(r"^(Resolved|Reduced|Improved|Managed|Achieved|Delivered|Optimized|Automated|Designed|Implemented)\b", text, re.I)
    if m:
        verb = m.group(1)
        rest = text[m.end():].strip()
        pct = re.search(r"(\d+%)", rest)
        if pct:
            pv = pct.group(1)
            verb_lower = verb.lower()
            if verb_lower.startswith("optimi"):
                return f"{pv} OPTIMIZATION"
            elif verb_lower.startswith("automat"):
                return f"{pv} AUTOMATION"
            elif verb_lower.startswith("reduc"):
                return f"{pv} REDUCTION"
            elif verb_lower.startswith("improv"):
                return f"{pv} IMPROVEMENT"
            elif verb_lower.startswith("resolv"):
                return f"{pv} RESOLUTION"
            elif verb_lower.startswith("manag"):
                return f"{pv} MANAGEMENT"
            elif verb_lower.startswith("achiev"):
                return f"{pv} ACHIEVEMENT"
            elif verb_lower.startswith("deliver"):
                return f"{pv} DELIVERY"
            elif verb_lower.startswith("design"):
                return f"{pv} DESIGN"
            elif verb_lower.startswith("implement"):
                return f"{pv} IMPLEMENTATION"
            
            after_pct = rest[pct.end():]
            before_pct = rest[:pct.start()]
            # Key: prioritize before_pct keywords over after_pct (they're closer to the number)
            for kw in ["deployment","satisfaction","improvement","reduction","optimization","efficiency","performance","delivery","quality","rate","automation","uptime","maintenance"]:
                if kw in before_pct.lower():
                    return f"{pv} {kw.upper()}"
            for kw in ["deployment","satisfaction","improvement","reduction","optimization","efficiency","performance","delivery","quality","rate","automation","uptime","maintenance"]:
                if kw in after_pct.lower():
                    return f"{pv} {kw.upper()}"
            for kw in ["satisfaction","improvement","reduction","efficiency","performance","delivery"]:
                if kw in text.lower():
                    return f"{pv} {kw.upper()}"
            return f"{pv} IMPACT"
        num = re.search(r"(\d+[+]?|\d+)", rest)
        if num:
            nv = num.group(1)
            after_num = rest[num.end():]
            before_num = rest[:num.start()]
            # Prioritize before_num (closer to the number)
            for kw in ["deployment","resolution","support","handling","issues","tickets","tasks","cases","optimization","automation","performance","maintenance","operations","infrastructure","network","security","service","delivery","efficiency","reduction","improvement","installation","configuration","management"]:
                if kw in before_num.lower():
                    if kw == "issues":
                        return f"{nv} RESOLVED"
                    return f"{nv} {kw.upper()}"
            for kw in ["deployment","resolution","support","handling","issues","tickets","tasks","cases","optimization","automation","performance","maintenance","operations","infrastructure","network","security","service","delivery","efficiency","reduction","improvement","installation","configuration","management"]:
                if kw in after_num.lower():
                    if kw == "issues":
                        return f"{nv} RESOLVED"
                    return f"{nv} {kw.upper()}"
            for kw in ["deployment","automation","optimization","reduction","improvement","performance","maintenance","infrastructure","network","operations","security","service"]:
                if kw in rest.lower():
                    return f"{nv} {kw.upper()}"
            return f"{nv} IMPACT"
        for kw in ["network","performance","automation","maintenance","infrastructure","operations","security","system","solution","service","process","team"]:
            if kw in rest.lower():
                return f"{verb.upper()} {kw.upper()}"
        return f"{verb.upper()} EXCELLENCE"
    words = text.split()[:3]
    return " ".join(words).upper().rstrip(",.:")



def _wrap_in_sovereign_template(company_name, job_title, body_text="", highlights=None, user_details=None, email_log_id: str = "", cv_path: str = None):
    """Build a complete, well-formed HTML email template for job applications.
    
    Returns a full HTML document with proper structure including <body>, header
    with candidate info, body paragraphs, highlights, and tracking pixel.
    """
    # Resolve dynamic candidate details
    if user_details:
        name = user_details.get("name") or config.CANDIDATE_NAME
        candidate_email = user_details.get("email") or config.CANDIDATE_EMAIL
        phone = user_details.get("phone") or config.CANDIDATE_PHONE
        linkedin = user_details.get("linkedin") or user_details.get("linkedin_url") or config.CANDIDATE_LINKEDIN
        profession = user_details.get("profession") or user_details.get("target_title") or "Senior Network Engineer"
    else:
        name = config.CANDIDATE_NAME
        candidate_email = config.CANDIDATE_EMAIL
        phone = config.CANDIDATE_PHONE
        linkedin = config.CANDIDATE_LINKEDIN
        profession = "Senior Network Engineer"

    # Compute initials dynamically (e.g. Sam Salameh -> SS)
    def get_initials(full_name: str) -> str:
        if not full_name:
            return "SS"
        parts = [p.strip() for p in full_name.split() if p.strip()]
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return "SS"

    initials = get_initials(name)

    # Build cover letter body paragraphs
    body_html = ""
    if body_text:
        paragraphs = [p.strip() for p in body_text.replace("\r\n", "\n").split("\n\n") if p.strip()]
        for p in paragraphs:
            body_html += f"<p style=\"margin:20px 0;font-size:15px;color:#e2e8f0;line-height:1.8;\">{p}</p>\n"
    else:
        body_html = f"""<p style="margin:20px 0;font-size:15px;color:#e2e8f0;line-height:1.8;">
Dear Hiring Team,</p>
<p style="margin:20px 0;font-size:15px;color:#e2e8f0;line-height:1.8;">
I am writing to express my strong interest in the <strong>{job_title}</strong> position at <strong>{company_name}</strong>.</p>
<p style="margin:20px 0;font-size:15px;color:#e2e8f0;line-height:1.8;">
I look forward to the opportunity to discuss how my skills align with your team's needs.</p>\n"""

    # Highlights section (numbered achievements)
    highlights_html = ""
    if highlights and isinstance(highlights, list) and len(highlights) > 0:
        cards = ""
        for i, h in enumerate(highlights[:5], 1):
            title = _extract_highlight_title(str(h))
            desc = str(h).replace(title.lower().capitalize(), "", 1).strip().lstrip(":.- ")
            cards += f"""<tr>
<td style="vertical-align:top;padding:12px 16px;border-bottom:1px solid #1e293b;">
  <div style="color:#00ff88;font-weight:700;font-size:13px;margin-bottom:4px;">{title}</div>
  <div style="color:#94a3b8;font-size:14px;line-height:1.6;">{desc if desc else h}</div>
</td>
</tr>\n"""
        highlights_html = f"""<table style="width:100%;margin:24px 0;border-collapse:collapse;">
{cards}</table>\n"""

    # Quote from user_details
    quote_html = ""
    if user_details:
        quote = user_details.get("quote")
        if quote:
            quote_html = f"<blockquote style=\"border-left:3px solid #00ff88;margin:20px 0;padding:12px 20px;color:#94a3b8;font-style:italic;\">{quote}</blockquote>\n"

    # CV attachment message
    attach_html = ""
    if cv_path:
        attach_html = "<p style=\"margin:20px 0;font-size:14px;color:#94a3b8;\">📎 I have attached my CV for your review.</p>\n"
    elif user_details and user_details.get("tailored_cv"):
        attach_html = f"<pre style='font-family: Arial, sans-serif; white-space: pre-wrap; font-size:13px;color:#94a3b8;'>{user_details['tailored_cv']}</pre>\n"

    # Tracking pixel (configurable, spam-safe CSS background-image instead of img tag)
    tracking_pixel_html = ""
    if email_log_id and getattr(config, 'TRACKING_PIXEL_ENABLED', False):
        track_url = f"https://jhfguf.pythonanywhere.com/api/v2/campaign/track/{email_log_id}?px=1"
        tracking_pixel_html = f"<div style='width:0;height:0;overflow:hidden;background-image:url({track_url})'></div>"

    # Build the complete HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Application: {job_title} - {company_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" style="width:100%;max-width:640px;margin:0 auto;background-color:#0f0f17;">
  <tr>
    <td style="padding:32px 28px;">
      <!-- Header: Candidate Info -->
      <table role="presentation" style="width:100%;">
        <tr>
          <td style="vertical-align:middle;">
            <div style="color:#ffffff;font-size:22px;font-weight:700;">{name}</div>
            <div style="color:#64748b;font-size:14px;margin-top:6px;">{profession}</div>
          </td>
          <td style="text-align:right;vertical-align:middle;">
            <div style="display:inline-block;background:#00ff8820;color:#00ff88;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;">{initials}</div>
          </td>
        </tr>
      </table>
      <div style="height:1px;background:#1e293b;margin:20px 0;"></div>

      <!-- Contact Info -->
      <table role="presentation" style="width:100%;margin-bottom:24px;">
        <tr>
          <td style="color:#94a3b8;font-size:13px;">✉️ <a href="mailto:{candidate_email}" style="color:#94a3b8;text-decoration:none;">{candidate_email}</a></td>
          <td style="color:#94a3b8;font-size:13px;text-align:center;">📞 <a href="tel:{phone}" style="color:#94a3b8;text-decoration:none;">{phone}</a></td>
          {'<td style="color:#94a3b8;font-size:13px;text-align:right;">🔗 <a href="' + linkedin + '" style="color:#94a3b8;text-decoration:none;">LinkedIn</a></td>' if linkedin else '<td></td>'}
        </tr>
      </table>

      <!-- Job Reference -->
      <div style="background:#1a1a2e;border-radius:8px;padding:16px 20px;margin-bottom:24px;">
        <div style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Application For</div>
        <div style="color:#ffffff;font-size:16px;font-weight:600;">{job_title}</div>
        <div style="color:#00ff88;font-size:14px;">{company_name}</div>
      </div>

      <!-- Body -->
      {body_html}

      <!-- Quote -->
      {quote_html}

      <!-- Highlights -->
      {highlights_html}

      <!-- Attachment notice -->
      {attach_html}

      <!-- Signature -->
      <div style="margin-top:32px;padding-top:20px;border-top:1px solid #1e293b;">
        <div style="color:#ffffff;font-size:15px;font-weight:600;">Best regards,</div>
        <div style="color:#00ff88;font-size:16px;font-weight:700;margin-top:8px;">{name}</div>
        <div style="color:#94a3b8;font-size:13px;margin-top:4px;">{profession}</div>
      </div>

      <!-- Footer -->
      <div style="margin-top:40px;padding-top:16px;border-top:1px solid #1e293b;text-align:center;">
        <div style="color:#475569;font-size:11px;">Sent via JobHunt Pro · Automated Job Application System</div>
      </div>
    </td>
  </tr>
</table>
{tracking_pixel_html}
</body>
</html>"""
    return html




class RateLimiter:
    """Per-provider rate limiter with sliding window."""

    def __init__(self):
        self.sent_times: Dict[str, List[float]] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def can_send(self, provider: str, hourly_limit: int = 100) -> bool:
        async with self.lock:
            now = time.time()
            self.sent_times[provider] = [
                t for t in self.sent_times[provider] if now - t < 3600
            ]
            return len(self.sent_times[provider]) < hourly_limit

    async def record_send(self, provider: str):
        async with self.lock:
            self.sent_times[provider].append(time.time())

    async def get_count(self, provider: str) -> int:
        async with self.lock:
            now = time.time()
            self.sent_times[provider] = [
                t for t in self.sent_times[provider] if now - t < 3600
            ]
            return len(self.sent_times[provider])


class CircuitBreaker:
    """Circuit breaker for email providers."""

    def __init__(self):
        self._failures: Dict[str, int] = {}
        self._disabled_until: Dict[str, float] = {}
        self._max_failures = 5
        self._cooldown = 600  # 10 min cooldown (matches smart_scheduler)

    def record_failure(self, name: str):
        self._failures[name] = self._failures.get(name, 0) + 1
        if self._failures[name] >= self._max_failures:
            self._disabled_until[name] = time.time() + self._cooldown
            logger.warning(f"Circuit OPEN: {name} disabled for {self._cooldown}s")

    def record_success(self, name: str):
        self._failures.pop(name, None)
        self._disabled_until.pop(name, None)

    def is_available(self, name: str) -> bool:
        if name not in self._disabled_until:
            return True
        if time.time() > self._disabled_until[name]:
            self._disabled_until.pop(name, None)
            self._failures.pop(name, None)
            return True
        return False


class EmailValidator:
    """Email format and MX validation."""

    def validate(self, email: str) -> Tuple[bool, str]:
        if not email or not isinstance(email, str):
            return False, "empty"
        email = email.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "invalid_format"
        blocked = ['test.com', 'example.com', 'fake.com', 'spam.com', 'noreply@']
        for b in blocked:
            if b in email:
                return False, "blocked_domain"
        return True, "ok"


class EmailBuilder:
    """Build professional email messages with correct MIME structure."""

    @staticmethod
    def build(to_email: str, company: str, title: str, cover_html: str,
              attachments: Optional[list] = None, tracking_id: str = "",
              highlights: Optional[list] = None,
              user_details: Optional[dict] = None) -> Tuple[MIMEMultipart, str]:
        """Build properly structured MIME email with HTML rendering support.
        attachments: list of file paths to attach (CV PDF, cover letter PDF, etc.)
        Uses 'alternative' wrapping so email clients render HTML, not raw tags.
        highlights: optional list of achievement strings rendered as numbered cards."""
        
        # Determine candidate information
        if user_details:
            name = user_details.get("name") or config.CANDIDATE_NAME
            candidate_email = user_details.get("email") or config.CANDIDATE_EMAIL
            phone = user_details.get("phone") or config.CANDIDATE_PHONE
            profession = user_details.get("profession") or user_details.get("target_title") or "Senior Network Engineer"
        else:
            name = user_details.get("name") or config.CANDIDATE_NAME if user_details else config.CANDIDATE_NAME
            candidate_email = user_details.get("email") or config.CANDIDATE_EMAIL if user_details else config.CANDIDATE_EMAIL
            phone = user_details.get("phone") or config.CANDIDATE_PHONE if user_details else config.CANDIDATE_PHONE
            profession = "Senior Network Engineer"

        if title.startswith("Fwd: RE:"):
            subject = title
        else:
            subject = f"Application: {title} - {company}"

        # Delegate HTML generation to the single wrap_in_sovereign_template function to avoid duplication
        html_body = _wrap_in_sovereign_template(company, title, cover_html, highlights, user_details, email_log_id=tracking_id)

        # Plain text fallback (same content, no HTML)
        plain_text = f"""{name} - {profession}
Email: {candidate_email}
Phone: {phone}

{cover_html}

---
Tracking ID: {tracking_id}"""

        # CORRECT MIME structure:
        # multipart/mixed
        #   +-- multipart/alternative
        #   |     +-- text/plain  (fallback)
        #   |     +-- text/html   (rendered by modern clients)
        #   +-- application/pdf  (attachment)
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{name} <{candidate_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = f"{name} <{candidate_email}>"
        msg["Message-ID"] = f"<{tracking_id}.jobhuntpro@jobhuntpro.com>"
        msg["X-Mailer"] = "JobHuntPro/3.0"

        # CRITICAL: alternative wrapping so HTML renders properly
        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
        alt_part.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt_part)

        if attachments:
            for path in attachments:
                if path and os.path.exists(path):
                    with open(path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(path)
                        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                        msg.attach(part)

        return msg, subject


class EmailEngine:
    """Production email engine with retry, rate limiting, and rotation."""

    def __init__(self):
        self.validator = EmailValidator()
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter()
        self.scheduler = scheduler
        self.cv_path = config.CV_PATH
        self._hotmail_pool = None  # Lazy-init
        self._hotmail_pool_available = False
        self._register_active_providers()

    def _register_active_providers(self):
        """Register providers that have valid credentials."""
        for p in config.EMAIL_PROVIDERS:
            if p.get("user") and p.get("password"):
                self.scheduler.register_provider(p["name"])
                logger.info(f"Active provider: {p['name']}")
            else:
                logger.debug(f"Skipping provider (no creds): {p['name']}")

    def _ensure_hotmail_pool(self):
        """Lazy-init the Hotmail OAuth2 pool."""
        if self._hotmail_pool is not None:
            return
        try:
            from core.hotmail_pool import init, get_stats, send_email_sync
            init()
            stats = get_stats()
            if stats['active'] > 0:
                self._hotmail_pool = True  # non-None signals initialized
                self._hotmail_pool_available = True
                logger.info(f"HotmailPool active: {stats['active']}/{stats['total_accounts']} accounts, {stats['max_daily_capacity']}/day")
            else:
                self._hotmail_pool = True
                self._hotmail_pool_available = False
                logger.warning("HotmailPool loaded but 0 active accounts")
        except Exception as e:
            self._hotmail_pool = True
            self._hotmail_pool_available = False
            logger.warning(f"HotmailPool init failed: {e}")

    def _get_provider_config(self, provider: str) -> Dict:
        # Build from config.EMAIL_PROVIDERS list (env vars loaded in config.py)
        for p in config.EMAIL_PROVIDERS:
            if p["name"] == provider:
                return {
                    "smtp": p["server"],
                    "port": p["port"],
                    "login": p["user"],
                    "password": p["password"],
                    "name": p["name"],
                    "oauth2": p.get("oauth2", False),
                }
        return {}

    async def _send_via_smtp(self, provider: str, msg: MIMEMultipart) -> bool:
        config_data = self._get_provider_config(provider)
        if not config_data:
            logger.warning(f"No config for provider: {provider}")
            return False

        # ── Hotmail OAuth2 Pool (sync, runs in thread pool to not block) ──
        if config_data.get("oauth2"):
            self._ensure_hotmail_pool()
            if not self._hotmail_pool_available:
                logger.warning("HotmailPool unavailable")
                return False
            import concurrent.futures
            from core.hotmail_pool import send_email_sync
            msg_str = msg.as_string()
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                success, status, sender = await loop.run_in_executor(
                    pool, send_email_sync, msg["To"], msg_str
                )
            if success:
                logger.info(f"[HOTMAIL-OAUTH2] Sent via {sender}")
                return True
            logger.warning(f"[HOTMAIL-OAUTH2] Failed: {status}")
            return False

        import aiosmtplib
        try:
            # SPF Alignment: override From to match authenticated SMTP account
            # This prevents SPF failures from mismatched sender domains
            smtp_user = config_data["login"]
            sender_name_raw = config_data.get("name", "JobHunt Pro")
            # Extract human-readable name from original From header
            original_from = str(msg.get("From", ""))
            display_name = config.CANDIDATE_NAME
            try:
                # Preserve Reply-To before overriding From
                if not msg.get("Reply-To"):
                    msg["Reply-To"] = config.CANDIDATE_EMAIL
            except Exception:
                pass
            # Override From to match SMTP account (SPF alignment)
            del msg["From"]
            msg["From"] = f"{display_name} <{smtp_user}>"
            logger.debug(f"[SPF] From aligned: {display_name} <{smtp_user}>")

            # 100% True Async execution using aiosmtplib
            smtp_client = aiosmtplib.SMTP(
                hostname=config_data["smtp"],
                port=config_data["port"],
                use_tls=False,
                start_tls=True,
                timeout=30
            )
            await smtp_client.connect()
            await smtp_client.login(config_data["login"], config_data["password"])
            
            errors, message = await smtp_client.send_message(msg)
            await smtp_client.quit()
            
            if errors:
                logger.warning(f"[SMTP-ASYNC] Refused recipients via {config_data.get('name', '?')}: {errors}")
                return False
                
            logger.info(f"[SMTP-ASYNC] Successfully sent via {config_data.get('name', config_data['smtp'])}")
            return True
            
        except aiosmtplib.SMTPAuthenticationError:
            logger.error(f"[SMTP-ASYNC] Auth failed for {config_data.get('smtp', '?')}")
            return False
        except aiosmtplib.SMTPRecipientsRefused:
            logger.warning(f"[SMTP-ASYNC] Recipient refused via {config_data.get('smtp', '?')}")
            return False
        except Exception as e:
            logger.warning(f"[SMTP-ASYNC] Execution error via {provider}: {e}")
            return False

    async def _send_via_google_oauth(self, msg: MIMEMultipart, user_details: dict) -> Tuple[bool, str]:
        """Send email natively via Gmail API using the user's OAuth tokens."""
        import time
        import base64
        import requests
        
        access_token = user_details.get("oauth_access_token")
        refresh_token = user_details.get("oauth_refresh_token")
        expires_at = user_details.get("oauth_expires_at", 0)
        email = user_details.get("email")

        # Refresh token if expired
        if time.time() > expires_at - 300: # 5 minutes buffer
            if not refresh_token:
                return False, "Token expired and no refresh token available."
            
            GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
            GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
            
            resp = requests.post("https://oauth2.googleapis.com/token", data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            })
            if not resp.ok:
                return False, f"Failed to refresh token: {resp.text}"
            
            tokens = resp.json()
            access_token = tokens.get("access_token")
            expires_at = time.time() + tokens.get("expires_in", 3599)
            
            # Update DB using email
            try:
                from web.app_v2 import get_db
                conn = get_db()
                conn.execute(
                    "UPDATE users SET oauth_access_token=?, oauth_expires_at=? WHERE email=?",
                    (access_token, expires_at, email)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"[OAUTH] Failed to update refreshed token in DB: {e}")

        # Send via Gmail API
        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"raw": raw_msg}

        resp = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers=headers, json=payload)
        
        if resp.ok:
            return True, "sent_via_oauth"
        else:
            return False, f"Gmail API error: {resp.text}"

    async def _send_via_microsoft_oauth(self, msg: MIMEMultipart, user_details: dict) -> Tuple[bool, str]:
        """Send email natively via Microsoft Graph API using the user's OAuth tokens."""
        import time
        import base64
        import requests
        
        access_token = user_details.get("oauth_access_token")
        refresh_token = user_details.get("oauth_refresh_token")
        expires_at = user_details.get("oauth_expires_at", 0)
        email = user_details.get("email")

        # Refresh token if expired
        if time.time() > expires_at - 300: # 5 minutes buffer
            if not refresh_token:
                return False, "Token expired and no refresh token available."
            
            MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
            MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
            
            resp = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            })
            if not resp.ok:
                return False, f"Failed to refresh token: {resp.text}"
            
            tokens = resp.json()
            access_token = tokens.get("access_token")
            expires_at = time.time() + tokens.get("expires_in", 3599)
            
            # Update DB
            try:
                from web.app_v2 import get_db
                conn = get_db()
                conn.execute(
                    "UPDATE users SET oauth_access_token=?, oauth_expires_at=? WHERE email=?",
                    (access_token, expires_at, email)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"[OAUTH] Failed to update refreshed Microsoft token in DB: {e}")

        # Send via Microsoft Graph API
        raw_msg = base64.b64encode(msg.as_bytes()).decode('utf-8')
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "text/plain"}

        resp = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", headers=headers, data=raw_msg)
        
        # Microsoft returns 202 Accepted on success
        if resp.status_code in (200, 202):
            return True, "sent_via_oauth"
        else:
            return False, f"Microsoft Graph API error: {resp.text}"

    async def send_with_retry(self, provider: str, msg: MIMEMultipart,
                               max_retries: int = 3) -> Tuple[bool, str]:
        """Send email with exponential backoff retry."""
        # DRY RUN MODE: Save to file instead of sending
        dry_run = getattr(config, 'DRY_RUN', os.getenv("DRY_RUN", "true").lower() == "true")
        if dry_run:
            return await self._dry_run_send(provider, msg)

        # Skip immediately if circuit breaker says provider is open (broken)
        if not self.circuit_breaker.is_available(provider):
            logger.warning(f"Circuit OPEN for {provider} - skipping immediately")
            return False, f"circuit_open:{provider}"

        for attempt in range(max_retries):
            try:
                success = await self._send_via_smtp(provider, msg)
                if success:
                    self.circuit_breaker.record_success(provider)
                    self.scheduler.record_send(provider)
                    await self.rate_limiter.record_send(provider)
                    return True, provider

                self.circuit_breaker.record_failure(provider)
                self.scheduler.record_failure(provider)

                if attempt < max_retries - 1:
                    delay = (2 ** attempt) * 5 + random.uniform(0, 5)
                    logger.info(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s")
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Send attempt {attempt + 1} failed: {e}")
                if "No module named" in str(e) or "aiosmtplib" in str(e):
                    break
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt * 5)

        logger.error(f"All SMTP retries failed for {provider}. Cascading to Triple Redundancy HTTP fallbacks...")
        
        # Extract payload from msg for HTTP APIs
        to_email = msg.get("To", "")
        subject = msg.get("Subject", "")
        body_html = ""
        body_text = ""
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload: body_html = payload.decode("utf-8", errors="ignore")
                    elif content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload: body_text = payload.decode("utf-8", errors="ignore")
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    if content_type == "text/html":
                        body_html = payload.decode("utf-8", errors="ignore")
                    else:
                        body_text = payload.decode("utf-8", errors="ignore")
                        
            # Fallback 1: Brevo HTTP
            logger.info(f"[CASCADE] Attempting Brevo HTTP Fallback for {to_email}...")
            brevo_success = await asyncio.to_thread(send_email_via_brevo_http, to_email, subject, body_html, body_text)
            if brevo_success:
                return True, "brevo_http_fallback"
                
            # Fallback 2: SendGrid HTTP
            logger.info(f"[CASCADE] Attempting SendGrid HTTP Fallback for {to_email}...")
            sendgrid_success = await asyncio.to_thread(send_email_via_sendgrid_http, to_email, subject, body_html, body_text)
            if sendgrid_success:
                return True, "sendgrid_http_fallback"
                
        except Exception as ex:
            logger.error(f"[CASCADE] HTTP Fallback extraction/execution failed: {ex}")

        return False, "exhausted"

    async def _dry_run_send(self, provider: str, msg: MIMEMultipart) -> Tuple[bool, str]:
        """Save email to file instead of sending (dry run mode)."""
        try:
            sent_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sent_mails")
            os.makedirs(sent_dir, exist_ok=True)
            to_addr = msg.get("To", "unknown").replace("@", "_at_").replace(".", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subject = msg.get("Subject", "no_subject")[:50].replace(" ", "_").replace("/", "_")
            filename = f"{timestamp}_{to_addr}_{subject}.eml"
            filepath = os.path.join(sent_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(msg.as_string())
            self.scheduler.record_send(provider)
            self.circuit_breaker.record_success(provider)
            logger.info(f"[DRY RUN] Email saved: {filepath}")
            return True, provider
        except Exception as e:
            logger.error(f"[DRY RUN] Failed to save email: {e}")
            return False, str(e)

    async def send_application(self, to_email: str, company: str, title: str,
                                cover_html: str, cv_path: Optional[str] = None,
                                generate_cover_pdf: bool = True,
                                user_details: Optional[dict] = None) -> Tuple[bool, str]:
        """Send job application email with CV + optional cover letter PDF."""
        valid, reason = self.validator.validate(to_email)
        if not valid:
            return False, f"invalid: {reason}"

        # God-Tier Optimization: ALWAYS send immediately, bypass time-of-day blocks
        # should_send, block_reason = self.scheduler.should_send_now()
        # if not should_send:
        #     return False, f"blocked: {block_reason}"

        # Check provider availability BEFORE building the email (optimization)
        provider = await self.scheduler.wait_for_send_slot()
        if not provider:
            return False, "no_providers"

        can_send = await self.rate_limiter.can_send(provider)
        if not can_send:
            return False, f"rate_limited: {provider}"

        tracking_id = str(uuid.uuid4())[:12]

        # Generate cover letter PDF
        cover_pdf_path = None
        if generate_cover_pdf:
            try:
                from core.cover_pdf import generate_cover_pdf as gen_pdf
                cover_pdf_path = gen_pdf(company, title)
            except Exception as e:
                logger.warning(f"Cover PDF generation failed: {e}")

        # Build message with both CV and cover PDF
        attachment_paths = []
        if cv_path or self.cv_path:
            attachment_paths.append(cv_path or self.cv_path)
        if cover_pdf_path:
            attachment_paths.append(cover_pdf_path)

        # Get candidate profile highlights for the email
        highlights = None
        if user_details and "skills" in user_details:
            skills = user_details["skills"]
            if isinstance(skills, str):
                highlights = [s.strip() for s in skills.split(",") if s.strip()]
            elif isinstance(skills, list):
                highlights = skills

        if not highlights:
            try:
                from core.ai_tailor import CANDIDATE_PROFILE
                highlights = CANDIDATE_PROFILE.get("highlights", [])
            except ImportError:
                pass

        msg, subject = EmailBuilder.build(
            to_email, company, title, cover_html,
            attachment_paths, tracking_id, highlights,
            user_details=user_details
        )
        
        msg_id = str(msg.get("Message-ID", ""))

        can_use_oauth = False
        if user_details and user_details.get("user_id") and user_details.get("oauth_provider") in ["google", "microsoft"] and user_details.get("oauth_access_token"):
            try:
                from web.app_v2 import get_db
                import datetime
                conn = get_db()
                today_start = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
                
                # Check how many emails sent by this user today (safeguard)
                count_row = conn.execute(
                    "SELECT COUNT(*) FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.sent_at >= ?",
                    (user_details["user_id"], today_start)
                ).fetchone()
                
                daily_sent = count_row[0] if count_row else 0
                conn.close()
                
                if daily_sent < 40:
                    can_use_oauth = True
                else:
                    logger.warning(f"OAuth safety limit reached for user {user_details['user_id']} ({daily_sent} sent today). Falling back to system SMTP to protect account.")
            except Exception as e:
                logger.error(f"Failed to check OAuth daily limit: {e}")
                can_use_oauth = False

        if can_use_oauth and user_details.get("oauth_provider") == "google":
            success, result = await self._send_via_google_oauth(msg, user_details)
            if success:
                logger.info(f"Email sent to {company} via Google OAuth (tracking: {tracking_id})")
                return True, f"{tracking_id}|{msg_id}"
            else:
                logger.warning(f"Google OAuth sending failed: {result}. Falling back to default provider...")

        if can_use_oauth and user_details.get("oauth_provider") == "microsoft":
            success, result = await self._send_via_microsoft_oauth(msg, user_details)
            if success:
                logger.info(f"Email sent to {company} via Microsoft OAuth (tracking: {tracking_id})")
                return True, f"{tracking_id}|{msg_id}"
            else:
                logger.warning(f"Microsoft OAuth sending failed: {result}. Falling back to default provider...")

        success, result = await self.send_with_retry(provider, msg)

        if success:
            logger.info(f"Email sent to {company} via {provider} (tracking: {tracking_id})")
            return True, f"{tracking_id}|{msg_id}"
        else:
            logger.warning(f"Email failed to {company}: {result}")
            return False, result

    async def send_followup(self, to_email: str, company: str, title: str,
                             original_date: str, followup_num: int = 1) -> Tuple[bool, str]:
        """Send follow-up email."""
        prefix = "Second" if followup_num > 1 else "First"
        subject = f"{prefix} Follow-up: {title} Application at {company}"

        tracking_id = str(uuid.uuid4())[:12]

        body = f"""<p>Dear Hiring Team,</p>
<p>I hope this message finds you well. I am writing to follow up on my application for the <strong>{title}</strong>
position at <strong>{company}</strong>, submitted on {original_date}.</p>
<p>With over 15 years of network engineering experience across Cisco, MikroTik, Fortinet, and Ubiquiti platforms,
I remain very interested in this opportunity.</p>
<p>I would appreciate any update regarding the status of my application.</p>
<p>Best regards,<br><strong>{config.CANDIDATE_NAME}</strong><br>{config.CANDIDATE_EMAIL}<br>{config.CANDIDATE_PHONE}</p>
<img src="https://jhfguf.pythonanywhere.com/api/v2/campaign/track/{tracking_id}" width="1" height="1" style="display:none" alt=""/>"""
        msg = MIMEMultipart()
        msg["From"] = f"{user_details.get('name', config.CANDIDATE_NAME)} <{config.CANDIDATE_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = f"{user_details.get('name', config.CANDIDATE_NAME)} <{config.CANDIDATE_EMAIL}>"
        msg["Message-ID"] = f"<{tracking_id}.followup@jobhuntpro.com>"

        msg.attach(MIMEText(body, "html", "utf-8"))

        provider = await self.scheduler.wait_for_send_slot()
        if not provider:
            return False, "no_providers"

        success, result = await self.send_with_retry(provider, msg)
        return success, tracking_id if success else result

    async def send_bulk(self, recipients: List[Dict], cover_html: str,
                         cv_path: Optional[str] = None) -> Dict[str, int]:
        """Send bulk emails with rate limiting."""
        results = {"sent": 0, "failed": 0, "skipped": 0}

        for recipient in recipients:
            to_email = recipient.get("email", "")
            company = recipient.get("company", "Unknown")
            title = recipient.get("title", "Position")

            if not to_email:
                results["skipped"] += 1
                continue

            success, _ = await self.send_application(to_email, company, title, cover_html, cv_path)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

            await asyncio.sleep(self.scheduler.calculate_delay())

        return results

    def get_stats(self) -> Dict:
        return {
            "scheduler": self.scheduler.get_stats(),
            "circuit_breaker": {
                "failures": dict(self.circuit_breaker._failures),
                "disabled": list(self.circuit_breaker._disabled_until.keys()),
            }
        }


    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str = "",
        body_text: str = "",
        from_name: str = "",
    ) -> bool:
        """
        Simple email send used by service delivery/fulfillment.
        Builds a MIME message and sends via the engine infrastructure.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{from_name or user_details.get('name', config.CANDIDATE_NAME)} <{config.CANDIDATE_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg["Reply-To"] = config.CANDIDATE_EMAIL

            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))
            elif body_text:
                msg.attach(MIMEText(body_text.replace("\n", "<br>\n"), "html", "utf-8"))

            provider = await self.scheduler.wait_for_send_slot()
            if not provider:
                logger.warning(f"No provider available for delivery email to {to_email}")
                return False

            can_send = await self.rate_limiter.can_send(provider)
            if not can_send:
                logger.warning(f"Rate limited for {provider}, delivery email to {to_email}")
                return False

            success, _ = await self.send_with_retry(provider, msg)
            return success

        except Exception as e:
            logger.error(f"send_email failed: {e}")
            return False


email_engine = EmailEngine()


class AntiGhostingEngine:
    """Automatic follow-up engine for non-responsive companies."""

    def __init__(self):
        self.email_engine = email_engine  # reuse module-level singleton for shared circuit-breaker & rate-limiter
        self.followup_days = [4, 7, 14]
        self.max_followups = 3

    async def check_and_send_followups(self, db):
        """Check for emails that need follow-up and send them."""
        try:
            from core.response_parser import followup_engine
            from datetime import timedelta

            now = datetime.utcnow()
            results = {"checked": 0, "sent": 0, "skipped": 0, "failed": 0}

            logger.info("Anti-ghosting: Checking for follow-ups...")

            campaigns = await db.get_user_campaigns("admin", limit=100)
            for campaign in campaigns:
                if campaign["status"] not in ("running", "completed"):
                    continue

                campaign_id = campaign["campaign_id"]

                try:
                    emails = await db.get_campaign_emails(campaign_id)
                    for email_record in emails:
                        results["checked"] += 1

                        if email_record["status"] in ("interview", "offer", "rejection"):
                            results["skipped"] += 1
                            continue

                        sent_at = email_record.get("sent_at")
                        if not sent_at:
                            continue

                        if isinstance(sent_at, str):
                            sent_at = datetime.fromisoformat(sent_at.replace("Z", "+00:00")).replace(tzinfo=None)

                        days_since = (now - sent_at).days
                        followup_count = email_record.get("followup_count", 0)

                        if followup_engine.should_send_followup(
                            days_since=days_since,
                            followup_count=followup_count,
                            last_response_type=email_record.get("response_type", "unknown")
                        ):
                            company = email_record.get("company_name", "the company")
                            title = email_record.get("job_title", "the position")
                            to_email = email_record.get("email_address", "")

                            if not to_email:
                                results["skipped"] += 1
                                continue

                            followup_text = followup_engine.get_followup(
                                company=company,
                                title=title,
                                followup_number=followup_count + 1,
                                days_since_application=days_since
                            )

                            success, _ = await self.email_engine.send_followup(
                                to_email=to_email,
                                company=company,
                                title=title,
                                original_date=sent_at.strftime("%Y-%m-%d"),
                                followup_num=followup_count + 1
                            )

                            if success:
                                results["sent"] += 1
                                logger.info(f"Follow-up #{followup_count+1} sent to {company}")
                            else:
                                results["failed"] += 1

                            await asyncio.sleep(self.email_engine.scheduler.calculate_delay())

                except Exception as e:
                    logger.error(f"Follow-up check error for campaign {campaign_id}: {e}")

            logger.info(f"Anti-ghosting results: {results}")
            return results

        except Exception as e:
            logger.error(f"Anti-ghosting engine error: {e}")
            return {"error": str(e)}

    async def auto_reply_interview(self, db, tracking_id: str, reply_text: str):
        """Auto-reply to interview requests with Calendly link."""
        try:
            from core.response_parser import parser

            email_record = await db.get_campaign_email_by_tracking(tracking_id)
            if not email_record:
                logger.warning(f"No email found for tracking_id: {tracking_id}")
                return False

            to_email = email_record.get("email_address", "")
            company = email_record.get("company_name", "the company")

            if not to_email:
                return False

            provider = self.email_engine.scheduler.get_next_provider()
            if not provider:
                logger.warning("No provider available for auto-reply")
                return False

            success, result = await self.email_engine.send_with_retry(
                provider,
                self._build_reply_message(to_email, company, reply_text)
            )

            if success:
                logger.info(f"Auto-reply sent to {company} for interview")
                await db.update_campaign_email_status(
                    tracking_id=tracking_id,
                    status="interview_replied"
                )

            return success

        except Exception as e:
            logger.error(f"Auto-reply error: {e}")
            return False

    def _build_reply_message(self, to_email: str, company: str, body: str) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = f"{user_details.get('name', config.CANDIDATE_NAME)} <{config.CANDIDATE_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = f"Re: Interview Scheduling - {company}"
        msg["Reply-To"] = f"{user_details.get('name', config.CANDIDATE_NAME)} <{config.CANDIDATE_EMAIL}>"
        msg.attach(MIMEText(body, "html", "utf-8"))
        return msg




# ── Brevo REST API (HTTP) ──────────────────────────────────────────────────

def send_email_via_brevo_http(
    to_email: str,
    company_name: str = "",
    job_title: str = "",
    custom_body: str = "",
    sender_name: str = config.CANDIDATE_NAME,
    subject: str = None,
) -> bool:
    """Send email via Brevo REST API (no SMTP needed).
    Uses BREVO_API_KEY from .env.
    Falls back to GMAIL_SMTP_USER as sender if BREVO_ACCOUNT_EMAIL not set.
    """
    api_key = config.BREVO_API_KEY
    if not api_key:
        logger.warning("[BREVO-HTTP] BREVO_API_KEY not configured")
        return False

    sender_email = (
        os.getenv("BREVO_ACCOUNT_EMAIL", "").strip()
        or os.getenv("GMAIL_SMTP_USER", "samsalameh.cv@gmail.com").strip()
    )
    if not sender_email:
        logger.warning("[BREVO-HTTP] No sender email configured")
        return False

    if not subject:
        subject = f"Application Update - {company_name}" if company_name else "JobHunt Pro Update"

    # Build HTML body
    if custom_body:
        html_body = custom_body
    else:
        html_body = (
            f"<h2>{subject}</h2>"
            f"<p>Hello,</p>"
            f"<p>This is an automated message from JobHunt Pro.</p>"
        )

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        if resp.status_code in (200, 201, 202):
            logger.info(f"[BREVO-HTTP] Sent to {to_email} — {subject}")
            return True
        else:
            logger.warning(f"[BREVO-HTTP] Failed: {resp.status_code} — {resp.text[:200]}")
            return False
    except Exception as e:
        logger.warning(f"[BREVO-HTTP] Error sending to {to_email}: {e}")
        return False

def send_email_via_sendgrid_http(
    to_email: str,
    subject: str = None,
    body_html: str = "",
    body_text: str = "",
) -> bool:
    """Send email via SendGrid REST API (no SMTP needed).
    Uses SENDGRID_API_KEY from .env.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        logger.warning("[SENDGRID-HTTP] SENDGRID_API_KEY not configured")
        return False

    sender_email = os.getenv("SENDGRID_SENDER_EMAIL", "samsalameh.cv@gmail.com").strip()

    if not subject:
        subject = "JobHunt Pro Update"

    if not body_html and not body_text:
        body_text = "This is an automated message from JobHunt Pro."

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": sender_email, "name": config.CANDIDATE_NAME},
        "subject": subject,
        "content": []
    }
    
    if body_text:
        payload["content"].append({"type": "text/plain", "value": body_text})
    if body_html:
        payload["content"].append({"type": "text/html", "value": body_html})

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        if resp.status_code in (200, 201, 202, 204):
            logger.info(f"[SENDGRID-HTTP] Sent to {to_email} — {subject}")
            return True
        else:
            logger.warning(f"[SENDGRID-HTTP] Failed: {resp.status_code} — {resp.text[:200]}")
            return False
    except Exception as e:
        logger.warning(f"[SENDGRID-HTTP] Error sending to {to_email}: {e}")
        return False


def send_email_via_gmail_smtp(
    to_email: str,
    company_name: str,
    job_title: str,
    custom_body: str,
    sender_name: str = config.CANDIDATE_NAME,
    subject: str = None,
    reply_to: str = None,
    sender_email: str = None,
    smtp_user: str = None,
    smtp_pass: str = None,
) -> bool:
    """Send via Gmail SMTP with app password. 15s timeout, TLS."""
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    if not smtp_user or not smtp_pass:
        return False
    
    if not sender_email:
        sender_email = smtp_user
    if not subject:
        subject = f"Application: {job_title} at {company_name}" if company_name else "Job Application"
    
    try:
        import email.utils
        msg = MIMEMultipart("alternative")
        msg_id = email.utils.make_msgid(domain=smtp_user.split('@')[-1] if '@' in smtp_user else 'gmail.com')
        msg["Message-ID"] = msg_id
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(custom_body, "html", "utf-8"))
        
        # Add attachments if any
        if attachment_paths:
            import os
            from email.mime.base import MIMEBase
            from email import encoders
            if isinstance(attachment_paths, str):
                attachment_paths = [attachment_paths]
            for path in attachment_paths:
                if path and os.path.exists(path):
                    try:
                        with open(path, "rb") as att:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(att.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(path)
                            part.add_header("Content-Disposition", f"attachment; filename={filename}")
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"[GMAIL-SMTP] Failed to attach {path}: {e}")

        pwd_clean = smtp_pass.replace(" ", "")
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
            s.starttls(context=ctx)
            s.login(smtp_user, pwd_clean)
            s.send_message(msg)
        logger.info(f"[GMAIL-SMTP] Sent to {to_email} via {smtp_user} with Message-ID {msg_id}")
        return True, msg_id
    except Exception as e:
        logger.warning(f"[GMAIL-SMTP] Failed to {to_email} via {smtp_user}: {e}")
        return False, str(e)


def send_email_via_resend(
    to_email: str,
    company_name: str,
    job_title: str,
    custom_body: str,
    attachment_paths=None,
    sender_name: str = config.CANDIDATE_NAME,
    highlights=None,
    subject: str = None,
    reply_to: str = None,
) -> bool:
    """[RESEND API] Best Gmail inbox delivery. Uses HTTP port 443.

    Supports 3 Resend keys (RESEND_API_KEY, RESEND_API_KEY_2, RESEND_API_KEY_3).
    Requires a verified custom domain in RESEND_FROM_EMAIL.
    """
    try:
        import resend as resend_lib
    except ImportError:
        logger.warning("[RESEND] resend package not installed. Run: pip install resend")
        return False

    # Collect all configured Resend keys
    resend_keys = []
    for env_var in ["RESEND_API_KEY", "RESEND_API_KEY_2", "RESEND_API_KEY_3"]:
        key = os.getenv(env_var, "").strip()
        if key:
            resend_keys.append((env_var, key))

    if not resend_keys:
        return False

    resend_from_email = os.getenv("RESEND_FROM_EMAIL", "").strip()
    if not resend_from_email:
        logger.debug("[RESEND] Skipped: RESEND_FROM_EMAIL not set (need verified domain).")
        return False

    if not subject:
        subject = f"Application: {job_title} - {company_name}"

    html_content = custom_body if custom_body else f"""
    <p>Dear Hiring Team,</p>
    <p>I am writing to express my interest in the <strong>{job_title}</strong> position at <strong>{company_name}</strong>.</p>
    <p>Best regards,<br><strong>{sender_name}</strong></p>
    """

    from_addr = f"{sender_name} <{resend_from_email}>"
    gmail_user = os.getenv("GMAIL_SMTP_USER", "").strip()

    # Build attachments
    attachments = []
    if attachment_paths:
        for path in attachment_paths if isinstance(attachment_paths, list) else [attachment_paths]:
            if path and os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        content = base64.b64encode(f.read()).decode("utf-8")
                        attachments.append({"filename": os.path.basename(path), "content": content})
                except Exception as e:
                    logger.warning(f"[RESEND] Failed to attach {path}: {e}")

    # Try each Resend key
    for env_var, key in resend_keys:
        try:
            resend_lib.api_key = key
            params = {
                "from": from_addr,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "reply_to": reply_to or gmail_user or to_email,
            }
            if attachments:
                params["attachments"] = attachments

            logger.info(f"[RESEND] Sending via {env_var} to {to_email}...")
            r = resend_lib.Emails.send(params)

            if r and r.get("id"):
                logger.info(f"[RESEND] SUCCESS! Email ID: {r.get('id')}")
                return True
        except Exception as e:
            logger.warning(f"[RESEND] {env_var} failed: {e}")
            continue

    return False


def send_email_via_mailjet(
    to_email: str,
    company_name: str,
    job_title: str,
    custom_body: str,
    attachment_paths=None,
    sender_name: str = config.CANDIDATE_NAME,
    highlights=None,
    subject: str = None,
    reply_to: str = None,
) -> bool:
    """[MAILJET API] Free 200/day. Uses HTTP port 443 — works on cloud."""
    api_key = os.getenv("MAILJET_API_KEY", "").strip()
    api_secret = os.getenv("MAILJET_API_SECRET", "").strip()
    if not api_key or not api_secret:
        return False

    if not subject:
        subject = f"Application: {job_title} - {company_name}"

    html_content = custom_body if custom_body else f"""
    <p>Dear Hiring Team,</p>
    <p>I am writing to express my interest in the <strong>{job_title}</strong> position at <strong>{company_name}</strong>.</p>
    <p>Best regards,<br><strong>{sender_name}</strong></p>
    """

    sender_email = os.getenv("GMAIL_SMTP_USER", "").strip()
    if not sender_email:
        return False

    attachment_list = []
    if attachment_paths:
        for path in attachment_paths if isinstance(attachment_paths, list) else [attachment_paths]:
            if path and os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        content = base64.b64encode(f.read()).decode("utf-8")
                        attachment_list.append({
                            "ContentType": "application/pdf",
                            "Filename": os.path.basename(path),
                            "Base64Content": content,
                        })
                except Exception as e:
                    logger.warning(f"[MAILJET] Failed to attach {path}: {e}")

    payload = {
        "Messages": [
            {
                "From": {"Email": sender_email, "Name": sender_name},
                "To": [{"Email": to_email}],
                "Subject": subject,
                "HTMLPart": html_content,
                "ReplyTo": {"Email": reply_to or sender_email},
            }
        ]
    }
    if attachment_list:
        payload["Messages"][0]["Attachments"] = attachment_list

    try:
        logger.info(f"[MAILJET] Sending to {to_email}...")
        response = requests.post(
            "https://api.mailjet.com/v3.1/send",
            auth=(api_key, api_secret),
            json=payload,
            timeout=20,
        )
        if response.status_code in (200, 201):
            data = response.json()
            messages = data.get("Messages", [])
            if messages and messages[0].get("Status") == "success":
                logger.info(f"[MAILJET] Email sent successfully!")
                return True
        logger.warning(f"[MAILJET] Failed: {response.status_code} - {response.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"[MAILJET] Exception: {e}")
        return False


def send_email_via_sendpulse(
    to_email: str,
    company_name: str,
    job_title: str,
    custom_body: str,
    attachment_paths=None,
    sender_name: str = config.CANDIDATE_NAME,
    highlights=None,
    subject: str = None,
    reply_to: str = None,
) -> bool:
    """[PORTED FROM CHRONOS] SendPulse HTTP API — free 12,000/month (~400/day)."""
    api_key = os.getenv("SENDPULSE_API_KEY", "").strip()
    client_id = os.getenv("SENDPULSE_CLIENT_ID", "").strip()
    client_secret = os.getenv("SENDPULSE_CLIENT_SECRET", "").strip()

    if not api_key and not (client_id and client_secret):
        return False

    if not subject:
        subject = f"Application: {job_title} - {company_name}"

    html_content = custom_body if custom_body else f"""
    <p>Dear Hiring Team,</p>
    <p>I am writing to express my interest in the <strong>{job_title}</strong> position at <strong>{company_name}</strong>.</p>
    <p>Best regards,<br><strong>{sender_name}</strong></p>
    """

    sender_email = os.getenv("SENDPULSE_SENDER_EMAIL", "").strip() or config.CANDIDATE_EMAIL

    try:
        if api_key:
            token = api_key
        else:
            token_resp = requests.post(
                "https://api.sendpulse.com/oauth/access_token",
                json={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
                timeout=15,
            )
            if token_resp.status_code != 200:
                logger.warning(f"[SENDPULSE] Token failed: {token_resp.text[:200]}")
                return False
            token = token_resp.json().get("access_token")
            if not token:
                return False

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        attachments = {}
        if attachment_paths:
            for path in attachment_paths if isinstance(attachment_paths, list) else [attachment_paths]:
                if path and os.path.exists(path):
                    try:
                        with open(path, "rb") as f:
                            attachments[os.path.basename(path)] = base64.b64encode(f.read()).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"[SENDPULSE] Failed to attach {path}: {e}")

        payload = {
            "email": {
                "html": html_content,
                "text": re.sub(r'<[^>]+>', '', html_content)[:500],
                "subject": subject,
                "from": {"name": sender_name, "email": sender_email},
                "to": [{"name": to_email.split("@")[0], "email": to_email}],
                "reply_to": {"name": sender_name, "email": reply_to or sender_email},
            }
        }
        if attachments:
            payload["email"]["attachments_binary"] = attachments

        logger.info(f"[SENDPULSE] Sending via HTTP API to {to_email}...")
        response = requests.post(
            "https://api.sendpulse.com/smtp/emails", headers=headers, json=payload, timeout=20
        )
        if response.status_code in (200, 201, 202):
            logger.info(f"[SENDPULSE] Email sent successfully!")
            return True
        logger.warning(f"[SENDPULSE] Failed: {response.status_code} - {response.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"[SENDPULSE] Exception: {e}")
        return False


anti_ghosting = AntiGhostingEngine()

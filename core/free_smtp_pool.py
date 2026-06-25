"""
FREE SMTP POOL v1 — Ultimate Free Email Sending (10 APIs, $0 cost!)
======================================
Adds HTTP-based email sending via free API tiers.
Complements existing SMTP pool (Gmail, Outlook, Brevo, Hotmail, etc.)

APIs integrated (all free forever tiers):
1. Resend — 100 emails/day FREE
2. Mailgun — 100 emails/day FREE (flex plan)
3. Elastic Email — 100 emails/day FREE  
4. ZeptoMail — 100 emails/day FREE
5. turboSMTP — 200 emails/day (6,000/month) FREE
6. Mailjet — 200 emails/day (6,000/month) FREE
7. SendPulse — 15,000 emails/month (500/day) FREE
8. Brevo — 300 emails/day FREE (already in email_engine.py)
9. SendGrid — 100 emails/day FREE (already in email_engine.py)
10. Postmark — 100 emails FREE (first 100)

Total FREE capacity: ~1,500+ emails/day from HTTP APIs alone
Combined with 1000+ Hotmail SMTP: 100,000+ emails/day potential

Created: 2026-06-24 — Ultimate Deep Scan Session
"""

import os
import json
import logging
import time
import base64
import random
from typing import Dict, Optional, Tuple

try:
    import requests as http_requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)


class FreeSMTPPool:
    """Orchestrates all free HTTP-based email APIs."""

    def __init__(self):
        self._providers = []
        self._stats = {}
        self._init_providers()

    def _init_providers(self):
        """Auto-detect configured providers from env vars."""
        # Resend
        if os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL"):
            self._providers.append({
                "name": "resend",
                "daily_limit": 100,
                "weight": 5,  # Best deliverability
            })
            self._stats["resend"] = {"sent": 0, "failed": 0}

        # Mailgun (flex plan — 100/day)
        if os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN"):
            self._providers.append({
                "name": "mailgun",
                "daily_limit": 100,
                "weight": 4,
            })
            self._stats["mailgun"] = {"sent": 0, "failed": 0}

        # Elastic Email
        if os.getenv("ELASTIC_EMAIL_API_KEY"):
            self._providers.append({
                "name": "elastic_email",
                "daily_limit": 100,
                "weight": 3,
            })
            self._stats["elastic_email"] = {"sent": 0, "failed": 0}

        # ZeptoMail
        if os.getenv("ZEPTOMAIL_TOKEN"):
            self._providers.append({
                "name": "zeptomail",
                "daily_limit": 100,
                "weight": 3,
            })
            self._stats["zeptomail"] = {"sent": 0, "failed": 0}

        # turboSMTP (6,000/month = 200/day)
        if os.getenv("TURBOSMTP_USER") and os.getenv("TURBOSMTP_PASS"):
            self._providers.append({
                "name": "turbosmtp",
                "daily_limit": 200,
                "weight": 3,
            })
            self._stats["turbosmtp"] = {"sent": 0, "failed": 0}

        # Mailjet
        if os.getenv("MJ_APIKEY_PUBLIC") and os.getenv("MJ_APIKEY_PRIVATE"):
            self._providers.append({
                "name": "mailjet",
                "daily_limit": 200,
                "weight": 4,
            })
            self._stats["mailjet"] = {"sent": 0, "failed": 0}

        # SendPulse (15,000/month = 500/day)
        if os.getenv("SENDPULSE_CLIENT_ID") and os.getenv("SENDPULSE_CLIENT_SECRET"):
            self._providers.append({
                "name": "sendpulse",
                "daily_limit": 500,
                "weight": 5,
            })
            self._stats["sendpulse"] = {"sent": 0, "failed": 0}

        # Postmark
        if os.getenv("POSTMARK_SERVER_TOKEN"):
            self._providers.append({
                "name": "postmark",
                "daily_limit": 100,
                "weight": 3,
            })
            self._stats["postmark"] = {"sent": 0, "failed": 0}

        logger.info(f"[FreeSMTPPool] {len(self._providers)} HTTP APIs detected: "
                     f"{[p['name'] for p in self._providers]}")

    def has_providers(self) -> bool:
        return len(self._providers) > 0

    def get_provider_count(self) -> int:
        return len(self._providers)

    def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        from_name: str = "",
        attachments: list = None,
    ) -> Tuple[bool, str]:
        """
        Send email via the best available free HTTP API.
        Returns (success: bool, provider_used: str).
        """
        if not self._providers:
            return False, "no_providers"

        # Weighted random selection (respects daily limits)
        available = [
            p for p in self._providers
            if self._stats.get(p["name"], {}).get("sent", 0) < p["daily_limit"]
        ]
        if not available:
            return False, "all_daily_limits_reached"

        # Sort by weight (highest first) and pick top
        available.sort(key=lambda x: x["weight"], reverse=True)
        chosen = available[0]  # Weighted: pick best available

        provider = chosen["name"]
        try:
            success = self._send_via_provider(provider, to_email, subject, html_body, text_body, from_name, attachments)
            if success:
                self._stats[provider]["sent"] = self._stats.get(provider, {}).get("sent", 0) + 1
                return True, provider
            else:
                self._stats[provider]["failed"] = self._stats.get(provider, {}).get("failed", 0) + 1
                # Fallback to next provider
                if len(available) > 1:
                    fallback = available[1]
                    actual_sender_name = from_name or "Sam Salameh"
                    self._stats.setdefault(fallback["name"], {"sent": 0, "failed": 0})
                    fb_success = self._send_via_provider(fallback["name"], to_email, subject, html_body, text_body, actual_sender_name, attachments)
                    if fb_success:
                        self._stats[fallback["name"]]["sent"] = self._stats[fallback["name"]].get("sent", 0) + 1
                        return True, fallback["name"]
                return False, f"{provider}_failed"
        except Exception as e:
            logger.error(f"[FreeSMTPPool] {provider} exception: {e}")
            return False, f"{provider}_error"

    def _send_via_provider(
        self,
        provider: str,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        from_name: str = "",
        attachments: list = None,
    ) -> bool:
        """Route to specific provider implementation."""
        name = from_name or "Sam Salameh"
        text = text_body or html_body

        dispatch = {
            "mailgun": self._send_mailgun,
            "elastic_email": self._send_elastic_email,
            "zeptomail": self._send_zeptomail,
            "turbosmtp": self._send_turbosmtp,
            "postmark": self._send_postmark,
        }

        if provider in dispatch:
            return dispatch[provider](to_email, subject, html_body, text, name, attachments)

        # Resend, Mailjet, SendPulse are handled by existing functions in email_engine.py
        # Import and call them
        try:
            if provider == "resend":
                from core.email_engine import send_email_via_resend
                return send_email_via_resend(to_email, "JobHunt", subject, html_body, sender_name=name, attachments=attachments)
            elif provider == "mailjet":
                from core.email_engine import send_email_via_mailjet
                return send_email_via_mailjet(to_email, "JobHunt", subject, html_body, text, sender_name=name, attachments=attachments)
            elif provider == "sendpulse":
                from core.email_engine import send_email_via_sendpulse
                return send_email_via_sendpulse(to_email, "JobHunt", subject, html_body, text, sender_name=name, attachments=attachments)
        except ImportError as e:
            logger.warning(f"[FreeSMTPPool] Cannot import {provider} sender: {e}")
        return False

    # ═══════════════════════════════════════════════════════════════════
    # MAILGUN (FREE — 100 emails/day via flex plan, no credit card)
    # ═══════════════════════════════════════════════════════════════════
    def _send_mailgun(self, to_email, subject, html, text, from_name, atts):
        api_key = os.getenv("MAILGUN_API_KEY", "")
        domain = os.getenv("MAILGUN_DOMAIN", "")
        if not api_key or not domain:
            return False
        try:
            url = f"https://api.mailgun.net/v3/{domain}/messages"
            data = {
                "from": f"{from_name} <jobhunt@{domain}>",
                "to": to_email,
                "subject": subject,
                "html": html,
                "text": text[:500],
            }
            files = []
            if atts:
                for att in atts:
                    files.append(("attachment", (att["filename"], att["content"], att["content_type"])))
            
            if HAS_REQUESTS:
                resp = http_requests.post(url, auth=("api", api_key), data=data, files=files if files else None, timeout=15)
                return resp.status_code == 200
            else:
                import urllib.request
                import urllib.parse
                req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode('utf-8'))
                req.add_header("Authorization", "Basic " + base64.b64encode(f"api:{api_key}".encode('utf-8')).decode('utf-8'))
                resp = urllib.request.urlopen(req, timeout=15)
                return resp.getcode() == 200
        except Exception as e:
            logger.warning(f"[Mailgun] Send failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════
    # ELASTIC EMAIL (FREE — 100 emails/day)
    # ═══════════════════════════════════════════════════════════════════
    def _send_elastic_email(self, to_email, subject, html, text, from_name, atts):
        api_key = os.getenv("ELASTIC_EMAIL_API_KEY", "")
        if not api_key:
            return False
        try:
            payload = {
                "Recipients": {"To": [to_email]},
                "Content": {
                    "Subject": subject,
                    "Body": [{"ContentType": "HTML", "Content": html}],
                    "From": f"{from_name} <jobhunt@elasticemail.com>",
                },
            }
            if atts:
                attachments_list = []
                for att in atts:
                    attachments_list.append({
                        "BinaryContent": att["content_b64"],
                        "Name": att["filename"],
                        "ContentType": att["content_type"]
                    })
                payload["Content"]["Attachments"] = attachments_list

            if HAS_REQUESTS:
                resp = http_requests.post(
                    "https://api.elasticemail.com/v4/emails/transactional",
                    headers={
                        "X-ElasticEmail-ApiKey": api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=15,
                )
                return resp.status_code in (200, 201)
            else:
                import urllib.request
                req = urllib.request.Request(
                    "https://api.elasticemail.com/v4/emails/transactional",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "X-ElasticEmail-ApiKey": api_key,
                        "Content-Type": "application/json",
                    }
                )
                resp = urllib.request.urlopen(req, timeout=15)
                return resp.getcode() in (200, 201)
        except Exception as e:
            logger.warning(f"[ElasticEmail] Send failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════
    # ZEPTOMAIL (FREE — 100 emails/day, Zoho's transactional service)
    # ═══════════════════════════════════════════════════════════════════
    def _send_zeptomail(self, to_email, subject, html, text, from_name, atts):
        token = os.getenv("ZEPTOMAIL_TOKEN", "")
        if not token:
            return False
        try:
            payload = {
                "from": {"address": "jobhunt@zeptomail.com", "name": from_name},
                "to": [{"email_address": {"address": to_email}}],
                "subject": subject,
                "htmlbody": html,
            }
            if atts:
                attachments_list = []
                for att in atts:
                    attachments_list.append({
                        "content": att["content_b64"],
                        "mime_type": att["content_type"],
                        "name": att["filename"]
                    })
                payload["attachments"] = attachments_list

            if HAS_REQUESTS:
                resp = http_requests.post(
                    "https://api.zeptomail.com/v1.1/email",
                    headers={
                        "Authorization": token,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=15,
                )
                return resp.status_code in (200, 201, 202)
            else:
                import urllib.request
                req = urllib.request.Request(
                    "https://api.zeptomail.com/v1.1/email",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "Authorization": token,
                        "Content-Type": "application/json",
                    }
                )
                resp = urllib.request.urlopen(req, timeout=15)
                return resp.getcode() in (200, 201, 202)
        except Exception as e:
            logger.warning(f"[ZeptoMail] Send failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════
    # TURBOSMTP (FREE — 6,000/month = 200/day)
    # ═══════════════════════════════════════════════════════════════════
    def _send_turbosmtp(self, to_email, subject, html, text, from_name, atts):
        user = os.getenv("TURBOSMTP_USER", "")
        pwd = os.getenv("TURBOSMTP_PASS", "")
        if not user or not pwd:
            return False
        try:
            payload = {
                "from": f"{from_name} <{user}>",
                "to": [to_email],
                "subject": subject,
                "content": html,
                "html_content": html,
            }
            if atts:
                attachments_list = []
                for att in atts:
                    attachments_list.append({
                        "content": att["content_b64"],
                        "name": att["filename"],
                        "mime": att["content_type"]
                    })
                payload["attachments"] = attachments_list

            if HAS_REQUESTS:
                resp = http_requests.post(
                    "https://api.turbo-smtp.com/api/v2/mail/send",
                    headers={
                        "Authorization": f"Bearer {pwd}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=15,
                )
                return resp.status_code in (200, 201)
            else:
                import urllib.request
                req = urllib.request.Request(
                    "https://api.turbo-smtp.com/api/v2/mail/send",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "Authorization": f"Bearer {pwd}",
                        "Content-Type": "application/json",
                    }
                )
                resp = urllib.request.urlopen(req, timeout=15)
                return resp.getcode() in (200, 201)
        except Exception as e:
            logger.warning(f"[turboSMTP] Send failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════
    # POSTMARK (FREE — 100 emails, no credit card to start)
    # ═══════════════════════════════════════════════════════════════════
    def _send_postmark(self, to_email, subject, html, text, from_name, atts):
        server_token = os.getenv("POSTMARK_SERVER_TOKEN", "")
        if not server_token:
            return False
        try:
            payload = {
                "From": f"{from_name} <jobhunt@postmark.com>",
                "To": to_email,
                "Subject": subject,
                "HtmlBody": html,
                "TextBody": text[:500],
                "MessageStream": "outbound",
            }
            if atts:
                attachments_list = []
                for att in atts:
                    attachments_list.append({
                        "Name": att["filename"],
                        "Content": att["content_b64"],
                        "ContentType": att["content_type"]
                    })
                payload["Attachments"] = attachments_list

            if HAS_REQUESTS:
                resp = http_requests.post(
                    "https://api.postmarkapp.com/email",
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "X-Postmark-Server-Token": server_token,
                    },
                    json=payload,
                    timeout=15,
                )
                return resp.status_code == 200
            else:
                import urllib.request
                req = urllib.request.Request(
                    "https://api.postmarkapp.com/email",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "X-Postmark-Server-Token": server_token,
                    }
                )
                resp = urllib.request.urlopen(req, timeout=15)
                return resp.getcode() == 200
        except Exception as e:
            logger.warning(f"[Postmark] Send failed: {e}")
            return False

    def get_stats(self) -> Dict:
        """Return current usage stats for all providers."""
        return {
            "providers": len(self._providers),
            "total_sent": sum(s.get("sent", 0) for s in self._stats.values()),
            "total_failed": sum(s.get("failed", 0) for s in self._stats.values()),
            "per_provider": self._stats,
        }


# Singleton
_free_smtp_pool: Optional[FreeSMTPPool] = None


def get_free_smtp_pool() -> FreeSMTPPool:
    global _free_smtp_pool
    if _free_smtp_pool is None:
        _free_smtp_pool = FreeSMTPPool()
    return _free_smtp_pool

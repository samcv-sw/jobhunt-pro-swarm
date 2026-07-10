"""
JobHunt Pro — Email Follow-Up Automation v1.0
PAID feature: automated follow-up cycles for campaigns.
Manages follow-up scheduling, AI-generated messages via Groq, and activity logging.

Pricing tiers:
  - $4.99/campaign (up to 50 follow-ups)
  - $19.99/campaign (up to 200 follow-ups)
  - $49.99/campaign (up to 500 follow-ups)

Max 3 follow-ups per email (1 original + 2 follow-ups).
Cycle: Day 3 (soft check) → Day 7 (value-add) → Day 14 (final push).
"""

import hashlib
import logging
import os
import random
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)

GROQ_API_URL = os.getenv(
    "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
)


# Follow-up cycles in days after initial send
FOLLOW_UP_DAYS = [3, 5, 7, 10, 14]
MAX_FOLLOWUPS = 2  # max 2 follow-ups after the original email

# Pricing tiers mapping
FOLLOWUP_PRICING = {
    "starter": {"price": 4.99, "max_followups": 50, "name": "Follow-Up Starter"},
    "pro": {"price": 19.99, "max_followups": 200, "name": "Follow-Up Pro"},
    "enterprise": {
        "price": 49.99,
        "max_followups": 500,
        "name": "Follow-Up Enterprise",
    },
}

# AI follow-up tone templates by stage
FOLLOWUP_TONES = {
    1: {
        "name": "soft_check",
        "style": "gentle, warm, and polite — you're just checking in, not pushing",
        "subject_prefix": "Quick Follow-Up",
    },
    2: {
        "name": "value_add",
        "style": "confident and insightful — you're adding value by explaining your relevant skills",
        "subject_prefix": "Re",
    },
}

# Semantic cache for AI-generated messages ($0 token savings)
_AI_CACHE: dict[str, str] = {}
_GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"]

FOLLOWUP_SERVICE_ID = "follow-up-automation-starter"
FOLLOWUP_PACKAGE_IDS = [
    "follow-up-automation-starter",
    "follow-up-automation-pro",
    "follow-up-automation-enterprise",
]


class FollowUpAutomation:
    """Email follow-up automation engine — AI-powered, campaign-aware, paid feature."""

    def __init__(self, get_db_fn=None):
        self.get_db = get_db_fn
        self._groq_key = config.GROQ_API_KEY

    # ── Public API ─────────────────────────────────────────────────────────

    def _get_eligible_emails(self, conn: Any, campaign_id: str) -> list[Any]:
        """
        Retrieve emails eligible for follow-up in a campaign.

        Args:
            conn: The database connection.
            campaign_id: The campaign ID to check.

        Returns:
            A list of database rows representing eligible emails.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        cutoff = (now - timedelta(days=3)).isoformat()
        return conn.execute(
            """
            SELECT ce.*, c.user_id 
            FROM campaign_emails ce
            JOIN campaigns c ON ce.campaign_id = c.campaign_id
            WHERE ce.campaign_id = ?
              AND ce.status = 'sent'
              AND ce.sent_at <= ?
              AND ce.opened_at IS NULL
              AND ce.responded_at IS NULL
              AND COALESCE(ce.followup_count, 0) < ?
            ORDER BY ce.sent_at ASC
        """,
            (campaign_id, cutoff, MAX_FOLLOWUPS),
        ).fetchall()

    def _process_single_email(
        self,
        conn: Any,
        email_record: dict,
        campaign_id: str,
        user_id: str,
        now: datetime,
    ) -> tuple[str, int | None]:
        """
        Process and send a follow-up for a single email record.

        Args:
            conn: The database connection.
            email_record: A dictionary representing the email row.
            campaign_id: The campaign ID.
            user_id: The user ID.
            now: The current datetime.

        Returns:
            A tuple of (status, max_allowed_if_quota_reached). Status can be "sent", "skipped", "failed", or "quota_reached".
        """
        followup_num = email_record.get("followup_count", 0) + 1

        if followup_num > MAX_FOLLOWUPS:
            return "skipped", None

        # Check per-campaign follow-up quota
        user_tier = self._get_user_tier(conn, user_id)
        current_followups = self._get_campaign_followup_count(conn, campaign_id)
        max_allowed = FOLLOWUP_PRICING.get(
            user_tier, FOLLOWUP_PRICING["starter"]
        )["max_followups"]
        if current_followups >= max_allowed:
            return "quota_reached", max_allowed

        company = email_record.get("company_name", "the company")
        title = email_record.get("job_title", "the position")
        to_email = email_record.get("email_address", "")
        days_since = 0
        if email_record.get("sent_at"):
            try:
                sent_dt = datetime.fromisoformat(
                    email_record["sent_at"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                days_since = (now - sent_dt).days
            except Exception:
                days_since = 3

        if not to_email or "@" not in to_email:
            return "skipped", None

        # Generate AI follow-up message
        followup_body = self._generate_followup_message(
            company=company,
            title=title,
            followup_number=followup_num,
            days_since=days_since,
            user_name=config.CANDIDATE_NAME,
        )

        # Send the follow-up email
        success, result = self._send_followup(
            to_email=to_email,
            company=company,
            title=title,
            followup_num=followup_num,
            body_html=followup_body,
            original_msg_id=email_record.get("message_id"),
            conn=conn,
        )

        if success:
            # Update followup_count
            conn.execute(
                "UPDATE campaign_emails SET followup_count = ? WHERE id = ?",
                (followup_num, email_record["id"]),
            )
            # Log in email_campaign_log
            conn.execute(
                """
                INSERT INTO email_campaign_log (campaign_type, user_id, to_email, subject, status)
                VALUES (?, ?, ?, ?, 'sent')
            """,
                (
                    "followup",
                    user_id,
                    to_email,
                    f"Follow-up #{followup_num}: {title} at {company}",
                ),
            )
            conn.commit()
            logger.info(
                f"[FollowUp] Sent #{followup_num} to {company} ({to_email}) — campaign {campaign_id}"
            )
            return "sent", None
        else:
            logger.warning(
                f"[FollowUp] Failed #{followup_num} to {company}: {result}"
            )
            return "failed", None

    def check_and_followup(self, campaign_id: str) -> dict:
        """Check a campaign for emails needing follow-ups and send them.

        Args:
            campaign_id: The campaign ID to check.

        Returns:
            {"status": "ok", "sent": N, "skipped": N, "failed": N, "message": "..."}
        """
        conn = None
        try:
            if self.get_db:
                conn = self.get_db()
            else:
                from web.app_v2 import get_db as _get_db

                conn = _get_db()

            campaign_row = conn.execute(
                "SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)
            ).fetchone()
            if not campaign_row:
                return {
                    "status": "error",
                    "message": f"Campaign {campaign_id} not found",
                }
            campaign = dict(campaign_row)

            user_id = campaign.get("user_id", "admin")

            # Verify the user has purchased follow-up-automation
            has_access = self._check_user_access(conn, user_id)
            if not has_access:
                return {
                    "status": "error",
                    "message": "Follow-up automation not purchased. Unlock on /services page.",
                }

            emails = self._get_eligible_emails(conn, campaign_id)
            if not emails:
                return {
                    "status": "ok",
                    "sent": 0,
                    "skipped": 0,
                    "failed": 0,
                    "message": "No emails eligible for follow-up (need 3+ days since sent, no open/response, < 2 follow-ups).",
                }

            sent_count = 0
            skipped_count = 0
            failed_count = 0
            now = datetime.now(UTC).replace(tzinfo=None)

            for row in emails:
                email_record = dict(row)
                status, max_allowed = self._process_single_email(
                    conn, email_record, campaign_id, user_id, now
                )

                if status == "quota_reached":
                    user_tier = self._get_user_tier(conn, user_id)
                    return {
                        "status": "ok",
                        "sent": sent_count,
                        "skipped": skipped_count
                        + len(emails)
                        - sent_count
                        - skipped_count,
                        "failed": failed_count,
                        "message": f"Follow-up quota reached ({max_allowed} for {user_tier} tier). Upgrade for more.",
                    }
                elif status == "sent":
                    sent_count += 1
                elif status == "skipped":
                    skipped_count += 1
                elif status == "failed":
                    failed_count += 1

                # Pacing: 45-90s between follow-ups
                delay = random.uniform(45, 90)
                import time as _t

                _t.sleep(delay)

            conn.commit()
            return {
                "status": "ok",
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "message": f"Follow-up cycle complete. Sent: {sent_count}, Skipped: {skipped_count}, Failed: {failed_count}",
            }

        except Exception as e:
            logger.error(f"[FollowUp] check_and_followup error for {campaign_id}: {e}")
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            return {"status": "error", "message": str(e)}
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def schedule_followups(self) -> dict:
        """Schedule follow-ups for all active campaigns with paid access.
        Called periodically by the self-tick loop.
        """
        conn = None
        try:
            if self.get_db:
                conn = self.get_db()
            else:
                from web.app_v2 import get_db as _get_db

                conn = _get_db()

            now = datetime.now(UTC).replace(tzinfo=None)
            cutoff = (now - timedelta(days=3)).isoformat()

            # Find active campaigns (running or completed)
            campaigns = conn.execute(
                """
                SELECT DISTINCT c.campaign_id, c.user_id
                FROM campaigns c
                WHERE c.status IN ('running', 'completed')
                  AND c.created_at <= ?
            """,
                (cutoff,),
            ).fetchall()

            results = {
                "campaigns_checked": 0,
                "campaigns_processed": 0,
                "total_sent": 0,
            }
            for crow in campaigns:
                cid = crow["campaign_id"]
                results["campaigns_checked"] += 1
                result = self.check_and_followup(cid)
                if result.get("sent", 0) > 0:
                    results["campaigns_processed"] += 1
                    results["total_sent"] += result["sent"]

            return {"status": "ok", **results}

        except Exception as e:
            logger.error(f"[FollowUp] schedule_followups error: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def get_followup_stats(self, campaign_id: str) -> dict:
        """Get follow-up statistics for a specific campaign."""
        conn = None
        try:
            if self.get_db:
                conn = self.get_db()
            else:
                from web.app_v2 import get_db as _get_db

                conn = _get_db()

            # Total emails in campaign
            total = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()[0]

            # Emails with follow-ups sent
            with_followups = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id = ? AND followup_count > 0",
                (campaign_id,),
            ).fetchone()[0]

            # Total follow-ups sent
            total_followups = conn.execute(
                "SELECT COALESCE(SUM(followup_count), 0) FROM campaign_emails WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()[0]

            # Follow-up responses (emails that got response after follow-up)
            responded_after_followup = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id = ? AND followup_count > 0 AND responded_at IS NOT NULL",
                (campaign_id,),
            ).fetchone()[0]

            # Average follow-ups per email
            avg_followups = round(total_followups / total, 2) if total > 0 else 0

            return {
                "status": "ok",
                "campaign_id": campaign_id,
                "total_emails": total,
                "emails_with_followups": with_followups,
                "total_followups_sent": total_followups,
                "responses_after_followup": responded_after_followup,
                "avg_followups_per_email": avg_followups,
                "followup_response_rate": round(
                    responded_after_followup / with_followups * 100, 1
                )
                if with_followups > 0
                else 0,
            }

        except Exception as e:
            logger.error(f"[FollowUp] get_followup_stats error: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def get_campaigns_with_followup_access(self) -> list[str]:
        """Return campaign IDs whose users have follow-up automation active."""
        conn = None
        try:
            if self.get_db:
                conn = self.get_db()
            else:
                from web.app_v2 import get_db as _get_db

                conn = _get_db()

            placeholders = ",".join("?" * len(FOLLOWUP_PACKAGE_IDS))
            rows = conn.execute(
                f"""
                SELECT DISTINCT c.campaign_id 
                FROM campaigns c
                JOIN purchased_services ps ON c.user_id = ps.user_id
                WHERE ps.package_id IN ({placeholders})
                  AND ps.status = 'active'
                  AND c.status IN ('running', 'completed')
            """,
                (*FOLLOWUP_PACKAGE_IDS,),
            ).fetchall()

            return [r["campaign_id"] for r in rows]

        except Exception as e:
            logger.error(f"[FollowUp] get_campaigns_with_followup_access error: {e}")
            return []
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    # ── Internal Helpers ────────────────────────────────────────────────────

    def _check_user_access(self, conn, user_id: str) -> bool:
        """Check if user has purchased any follow-up-automation tier."""
        try:
            placeholders = ",".join("?" * len(FOLLOWUP_PACKAGE_IDS))
            row = conn.execute(
                f"SELECT 1 FROM purchased_services WHERE user_id = ? AND package_id IN ({placeholders}) AND status = 'active'",
                (user_id, *FOLLOWUP_PACKAGE_IDS),
            ).fetchone()
            return row is not None
        except Exception:
            return True  # Allow access if table doesn't exist (dev/testing)

    def _get_user_tier(self, conn, user_id: str) -> str:
        """Get user's follow-up pricing tier based on which package they purchased."""
        try:
            placeholders = ",".join("?" * len(FOLLOWUP_PACKAGE_IDS))
            row = conn.execute(
                f"SELECT package_id, price_paid FROM purchased_services WHERE user_id = ? AND package_id IN ({placeholders}) AND status = 'active' ORDER BY price_paid DESC LIMIT 1",
                (user_id, *FOLLOWUP_PACKAGE_IDS),
            ).fetchone()
            if row:
                pid = row[0]
                if "enterprise" in pid:
                    return "enterprise"
                elif "pro" in pid:
                    return "pro"
                else:
                    return "starter"
        except Exception:
            pass
        return "starter"

    def _get_campaign_followup_count(self, conn, campaign_id: str) -> int:
        """Get total follow-ups already sent for this campaign."""
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(followup_count), 0) FROM campaign_emails WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    def _generate_followup_message(
        self,
        company: str,
        title: str,
        followup_number: int,
        days_since: int,
        user_name: str = "Sam Salameh",
    ) -> str:
        """Generate AI-powered follow-up email body using Groq. Falls back to templates."""
        tone = FOLLOWUP_TONES.get(followup_number, FOLLOWUP_TONES[1])
        style = tone["style"]

        prompt = f"""You are a professional job application follow-up writer. Write a short, polite, professional follow-up email body for a {title} position at {company}.

Context:
- This is follow-up #{followup_number} (out of max 2 follow-ups)
- The original application was sent {days_since} days ago
- The candidate is {user_name}, a Senior Network Engineer with 15+ years of experience in Cisco, MikroTik, Fortinet, Ubiquiti
- Tone: {style}
- Important: Keep it 3-4 short paragraphs max. Use HTML <p> tags. No subject line needed — just the body.
- Mention the candidate's name ({user_name}) at the end.
- If follow-up #2, be slightly more direct but still warm.
- Return ONLY the HTML body paragraphs, nothing else."""

        # Check semantic cache
        cache_key = hashlib.md5(
            f"{company}|{title}|{followup_number}|{days_since}".encode()
        ).hexdigest()
        if cache_key in _AI_CACHE:
            logger.info(
                f"[FollowUp AI] Cache hit for {company} follow-up #{followup_number}"
            )
            return _AI_CACHE[cache_key]

        # Try Groq AI
        ai_body = self._call_groq(prompt)
        if ai_body and len(ai_body) > 50:
            _AI_CACHE[cache_key] = ai_body
            return ai_body

        # Fallback to template
        return self._get_template_body(
            company, title, followup_number, days_since, user_name
        )

    def _call_groq(self, prompt: str) -> str | None:
        """Call Groq API to generate follow-up text."""
        if not self._groq_key:
            return None

        url = GROQ_API_URL
        headers = {
            "Authorization": f"Bearer {self._groq_key}",
            "Content-Type": "application/json",
        }

        for model in _GROQ_MODELS:
            try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 600,
                }

                with httpx.Client(timeout=30) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        if content and len(content.strip()) > 30:
                            return content.strip()
                    elif resp.status_code == 429:
                        error_text = resp.text.lower()
                        if "tokens per day" in error_text or "tpd" in error_text:
                            logger.warning(
                                f"[FollowUp AI] Groq {model} TPD limit exhausted"
                            )
                            continue
                        logger.warning(f"[FollowUp AI] Groq rate limited on {model}")
                        continue
                    else:
                        logger.warning(
                            f"[FollowUp AI] Groq {model} error: {resp.status_code}"
                        )
                        continue
            except Exception as e:
                logger.warning(f"[FollowUp AI] Groq {model} failed: {e}")
                continue

        return None

    def _get_template_body(
        self,
        company: str,
        title: str,
        followup_number: int,
        days_since: int,
        user_name: str,
    ) -> str:
        """Static fallback templates for follow-up emails."""
        if followup_number == 1:
            return f"""<p>Dear Hiring Team at {company},</p>
<p>I hope this message finds you well. I wanted to kindly follow up on my application for the <strong>{title}</strong> position, which I submitted {days_since} days ago.</p>
<p>I remain very enthusiastic about this opportunity and would welcome the chance to discuss how my 15+ years of network engineering experience — spanning Cisco, MikroTik, Fortinet, and Ubiquiti — could contribute to {company}'s success.</p>
<p>Please let me know if you need any additional information from my side. I appreciate your time and consideration.</p>
<p>Best regards,<br><strong>{user_name}</strong></p>"""
        else:
            return f"""<p>Dear Hiring Team at {company},</p>
<p>I hope all is well. I wanted to follow up once more regarding my application for the <strong>{title}</strong> position submitted {days_since} days ago.</p>
<p>Since applying, I've been reflecting on how my expertise in enterprise network infrastructure, automation, and security could deliver immediate value to {company}. I remain genuinely interested and believe my background aligns well with what you're looking for.</p>
<p>I would still be very grateful for the opportunity to connect and discuss how I can contribute to your team. Thank you again for your consideration.</p>
<p>Warm regards,<br><strong>{user_name}</strong></p>"""

    def _send_followup(
        self,
        to_email: str,
        company: str,
        title: str,
        followup_num: int,
        body_html: str,
        original_msg_id: str = None,
        conn=None,
    ) -> tuple[bool, str]:
        """Send a follow-up email using the email engine."""
        try:
            from core.email_engine import EmailBuilder, EmailEngine

            engine = EmailEngine()

            prefix = "Second" if followup_num > 1 else "First"
            subject = f"{prefix} Follow-Up: {title} Application at {company}"

            tracking_id = f"fup_{hashlib.md5(f'{to_email}{company}{followup_num}'.encode()).hexdigest()[:12]}"

            msg, _ = EmailBuilder.build(
                to_email=to_email,
                company=company,
                title=title,
                cover_html=body_html,
                tracking_id=tracking_id,
                user_details={
                    "name": config.CANDIDATE_NAME,
                    "email": config.CANDIDATE_EMAIL,
                    "phone": config.CANDIDATE_PHONE,
                    "linkedin": config.CANDIDATE_LINKEDIN,
                    "profession": "Senior Network Engineer",
                },
            )

            # Override subject for follow-up
            if "Subject" in msg:
                del msg["Subject"]
            msg["Subject"] = subject
            if "Message-ID" in msg:
                del msg["Message-ID"]
            msg["Message-ID"] = f"<{tracking_id}.followup@jobhuntpro.com>"

            if original_msg_id:
                msg["In-Reply-To"] = original_msg_id
                msg["References"] = original_msg_id

            import asyncio as _asyncio

            async def send_it():
                provider = await engine.scheduler.wait_for_send_slot()
                if not provider:
                    return False, "no_providers"
                return await engine.send_with_retry(provider, msg, max_retries=2)

            success, provider = _asyncio.run(send_it())

            if success:
                return True, provider
            return False, provider

        except Exception as e:
            logger.error(f"[FollowUp] Send error to {company}: {e}")
            return False, str(e)


# Global singleton
followup_automation = FollowUpAutomation()


# ── Pricing Integration ────────────────────────────────────────────────────


def get_followup_pricing() -> list[dict]:
    """Return follow-up automation pricing tiers for the services page."""
    return [
        {
            "package": "follow-up-automation-starter",
            "tier": "starter",
            "name": "📬 Follow-Up Starter",
            "price_usd": 4.99,
            "description": "Up to 50 AI follow-ups per campaign. Day 3 & Day 7 — soft check + value-add. Groq AI generated.",
            "icon": "📬",
            "result": "+40% response rate",
            "max_followups": 50,
        },
        {
            "package": "follow-up-automation-pro",
            "tier": "pro",
            "name": "📬 Follow-Up Pro",
            "price_usd": 19.99,
            "description": "Up to 200 AI follow-ups per campaign. Full 2-cycle automation with personalized Groq AI messages.",
            "icon": "📬",
            "result": "+65% response rate",
            "max_followups": 200,
        },
        {
            "package": "follow-up-automation-enterprise",
            "tier": "enterprise",
            "name": "📬 Follow-Up Enterprise",
            "price_usd": 49.99,
            "description": "Up to 500 AI follow-ups per campaign. Maximum coverage with priority AI message generation.",
            "icon": "📬",
            "result": "+85% response rate",
            "max_followups": 500,
        },
    ]


def get_user_followup_quota(conn, user_id: str) -> dict:
    """Get user's follow-up quota and usage."""
    try:
        placeholders = ",".join("?" * len(FOLLOWUP_PACKAGE_IDS))
        row = conn.execute(
            f"SELECT package_id, price_paid FROM purchased_services WHERE user_id = ? AND package_id IN ({placeholders}) AND status = 'active' ORDER BY price_paid DESC LIMIT 1",
            (user_id, *FOLLOWUP_PACKAGE_IDS),
        ).fetchone()
        if not row:
            return {
                "has_access": False,
                "tier": None,
                "max_followups": 0,
                "used": 0,
                "remaining": 0,
            }

        pid = row[0]
        if "enterprise" in pid:
            tier_info = FOLLOWUP_PRICING["enterprise"]
            tier = "enterprise"
        elif "pro" in pid:
            tier_info = FOLLOWUP_PRICING["pro"]
            tier = "pro"
        else:
            tier_info = FOLLOWUP_PRICING["starter"]
            tier = "starter"

        # Count total follow-ups used across all campaigns
        used_row = conn.execute(
            "SELECT COALESCE(SUM(ce.followup_count), 0) FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ?",
            (user_id,),
        ).fetchone()
        used = used_row[0] if used_row else 0

        return {
            "has_access": True,
            "tier": tier,
            "max_followups": tier_info["max_followups"],
            "used": used,
            "remaining": max(0, tier_info["max_followups"] - used),
        }
    except Exception as e:
        logger.error(f"[FollowUp] get_user_followup_quota error: {e}")
        return {
            "has_access": False,
            "tier": None,
            "max_followups": 0,
            "used": 0,
            "remaining": 0,
        }

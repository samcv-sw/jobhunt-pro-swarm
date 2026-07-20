"""
Telegram Smart Auto-Notifications
Proactive alerts for job hunt activity

Monitors DB changes and pushes intelligent alerts:
- New employer responses (real-time)
- Interview invitations detected
- Follow-up reminders (5-day no-response, upcoming interviews)
- Application milestones (10, 50, 100 apps, first interview, first offer)
- Rate limit / quota warnings
"""

import asyncio
import os
import time

if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim as sqlite3
    except ImportError:
        import sqlite3
else:
    import sqlite3
import logging
import threading
from collections.abc import Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ── Milestone thresholds ──────────────────────────────────────────
MILESTONES = {
    10: {"emoji": "🔥", "label": "Double digits!"},
    50: {"emoji": "💯", "label": "Half century!"},
    100: {"emoji": "🏆", "label": "CENTURY!"},
    200: {"emoji": "🚀", "label": "200 — MACHINE!"},
    500: {"emoji": "👑", "label": "500 — LEGENDARY!"},
    1000: {"emoji": "🌟", "label": "1000 — IMMORTAL!"},
}

# Milestones we only fire ONCE ever
FIRST_TIME_MILESTONES = {
    "first_interview": ("🎯", "Breakthrough! First interview invitation!"),
    "first_offer": ("🎉", "YOU GOT AN OFFER! 🎉🎉🎉"),
}


class TelegramNotifier:
    """
    Background notification service.
    Monitors DB and pushes alerts via callbacks.

    Runs in a daemon thread — non-blocking, fire-and-forget.
    Checks DB every 5 minutes for new activity.
    """

    def __init__(self, db_path: str, send_callback: Callable):
        self.db_path = db_path
        self.send_callback = send_callback  # async function to send Telegram message
        self._running = False
        self._thread = None
        self._last_check = time.time()
        self.notified: set[int] = set()  # response IDs already alerted
        self._milestones_fired: set[str] = set()  # milestone keys already celebrated
        self._followups_sent: set[int] = (
            set()
        )  # application IDs we already sent follow-up for

    # ── Lifecycle ─────────────────────────────────────────────────

    def start(self):
        """Start background notification checker."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("[Notifier] Background notification service started")

    def stop(self):
        """Stop the notification loop gracefully."""
        self._running = False
        logger.info("[Notifier] Notification service stopped")

    # ── Main Loop ─────────────────────────────────────────────────

    def _run(self):
        """Main notification loop — checks all categories every 5 min."""
        while self._running:
            try:
                self._check_new_responses()
                self._check_interview_invites()
                self._check_follow_ups_due()
                self._check_upcoming_interviews()
                self._check_application_milestones()
                self._check_rate_limit_warnings()
            except Exception as e:
                logger.error(f"[Notifier] Loop error: {e}")
            time.sleep(300)  # 5 minutes

    # ── 1. New Employer Responses ─────────────────────────────────

    def _check_new_responses(self):
        """Check for new employer responses since last check."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Support both `responses` and `incoming_responses` tables
            rows = []
            try:
                c = conn.execute(
                    "SELECT id, company, status, message, created_at "
                    "FROM responses WHERE notified = 0 AND created_at > ?",
                    (self._last_check,),
                )
                rows = c.fetchall()
            except sqlite3.OperationalError:
                # Table might not exist yet
                pass

            for row in rows:
                rid = row["id"]
                if rid in self.notified:
                    continue
                company = row["company"] or "Unknown Company"
                status = row["status"] or "unknown"
                message = (row["message"] or "")[:200]
                self._send_alert(
                    f"📬 *New Response!*\n\n"
                    f"Company: *{company}*\n"
                    f"Status: {self._status_emoji(status)} {status}\n"
                    f"Message: {message}..."
                )
                self.notified.add(rid)
                conn.execute("UPDATE responses SET notified = 1 WHERE id = ?", (rid,))
                conn.commit()

            self._last_check = time.time()
        except Exception as e:
            logger.error(f"[Notifier] _check_new_responses error: {e}")
        finally:
            if conn:
                conn.close()

    # ── 2. Interview Invitations ──────────────────────────────────

    def _check_interview_invites(self):
        """Detect interview invitations from response messages."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                c = conn.execute(
                    "SELECT id, company, message FROM responses "
                    "WHERE (message LIKE '%interview%' OR message LIKE '%مقابلة%') "
                    "AND notified = 0"
                )
                rows = c.fetchall()
            except sqlite3.OperationalError:
                return

            for row in rows:
                rid = row["id"]
                if rid in self.notified:
                    continue
                company = row["company"] or "Unknown Company"
                self._send_alert(
                    f"🎯 *Interview Invitation!*\n\n"
                    f"Company: *{company}*\n"
                    f"💡 Schedule it via /calendar\n\n"
                    f"_Reply to this alert with your availability_"
                )
                self.notified.add(rid)
                conn.execute("UPDATE responses SET notified = 1 WHERE id = ?", (rid,))
                conn.commit()

                # Also fire first-interview milestone
                self._maybe_first_time_milestone("first_interview", company)
        except Exception as e:
            logger.error(f"[Notifier] _check_interview_invites error: {e}")
        finally:
            if conn:
                conn.close()

    # ── 3. Follow-Up Reminders ────────────────────────────────────

    def _check_follow_ups_due(self):
        """Check for applications with no response for 5+ days — suggest follow-up."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cutoff = (datetime.now() - timedelta(days=5)).isoformat()
            # Try common table/column names
            queries = [
                "SELECT id, company, job_title, applied_at FROM applications "
                "WHERE status = 'applied' AND applied_at <= ? AND id NOT IN "
                "(SELECT DISTINCT application_id FROM responses WHERE application_id IS NOT NULL)",
                "SELECT id, company, title AS job_title, created_at AS applied_at FROM leads "
                "WHERE status = 'applied' AND created_at <= ?",
            ]
            for q in queries:
                try:
                    c = conn.execute(q, (cutoff,))
                    rows = c.fetchall()
                    if rows:
                        break
                except sqlite3.OperationalError:
                    continue
            else:
                rows = []

            for row in rows:
                app_id = row["id"]
                if app_id in self._followups_sent:
                    continue
                company = row["company"] or "Unknown Company"
                job_title = row["job_title"] or "a position"
                self._send_alert(
                    f"⏰ *Time for a Follow-Up?*\n\n"
                    f"Applied to *{company}* ({job_title})\n"
                    f"5+ days ago — no response yet.\n\n"
                    f"💡 Send a polite follow-up email?\n"
                    f"_Use /followups for the full list_"
                )
                self._followups_sent.add(app_id)
            return
        except Exception as e:
            logger.error(f"[Notifier] _check_follow_ups_due error: {e}")
        finally:
            if conn:
                conn.close()

    # ── 4. Upcoming Interview Reminders ───────────────────────────

    def _check_upcoming_interviews(self):
        """Remind about interviews happening in the next 1-2 days."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            # Try interviews table
            for table in ("interviews", "calendar_events", "events"):
                try:
                    c = conn.execute(
                        f"SELECT id, company, interview_date, notes FROM {table} "
                        "WHERE interview_date IN (?, ?) AND reminded = 0",
                        (tomorrow, day_after),
                    )
                    rows = c.fetchall()
                    if rows:
                        for row in rows:
                            company = row["company"] or "Unknown Company"
                            when = row["interview_date"]
                            notes = (row["notes"] or "")[:100]
                            urgency = "tomorrow" if when == tomorrow else "in 2 days"
                            self._send_alert(
                                f"📅 *Interview {urgency}!*\n\n"
                                f"Company: *{company}*\n"
                                f"Date: {when}\n"
                                f"Notes: {notes}\n\n"
                                f"🎓 Prep with /prep"
                            )
                            conn.execute(
                                f"UPDATE {table} SET reminded = 1 WHERE id = ?",
                                (row["id"],),
                            )
                            conn.commit()
                        break
                except sqlite3.OperationalError:
                    continue
        except Exception as e:
            logger.error(f"[Notifier] _check_upcoming_interviews error: {e}")
        finally:
            if conn:
                conn.close()

    # ── 5. Application Milestones ─────────────────────────────────

    def _check_application_milestones(self):
        """Celebrate milestones: 10, 50, 100, 200, 500, 1000 applications."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Count total applications
            queries = [
                "SELECT COUNT(*) FROM applications",
                "SELECT COUNT(*) FROM leads WHERE status IN ('applied','sent')",
            ]
            count = 0
            for q in queries:
                try:
                    count = conn.execute(q).fetchone()[0]
                    if count > 0:
                        break
                except sqlite3.OperationalError:
                    continue

            for threshold, info in sorted(MILESTONES.items()):
                key = f"apps_{threshold}"
                if count >= threshold and key not in self._milestones_fired:
                    self._send_alert(
                        f"{info['emoji']} *{count} Applications Sent!*\n\n"
                        f"{info['label']}\n"
                        f"Keep the momentum going! 🚀"
                    )
                    self._milestones_fired.add(key)
        except Exception as e:
            logger.error(f"[Notifier] _check_application_milestones error: {e}")
        finally:
            if conn:
                conn.close()

    # ── 6. Rate Limit / Quota Warnings ────────────────────────────

    def _check_rate_limit_warnings(self):
        """Warn about approaching email/Gmail rate limits or low API quota."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Check email send rate in last hour
            try:
                one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                sent_last_hour = conn.execute(
                    "SELECT COUNT(*) FROM campaign_emails WHERE sent_at >= ?",
                    (one_hour_ago,),
                ).fetchone()[0]
            except sqlite3.OperationalError:
                sent_last_hour = 0

            if sent_last_hour >= 80:
                self._send_alert(
                    f"⚠️ *Rate Limit Warning!*\n\n"
                    f"{sent_last_hour} emails sent in the last hour.\n"
                    f"Gmail daily limit: 500 (free), 2000 (Workspace).\n"
                    f"Consider spreading out sends or switching providers."
                )
            elif sent_last_hour >= 400:
                self._send_alert(
                    f"🚨 *CRITICAL: Rate Limit Risk!*\n\n"
                    f"{sent_last_hour} emails in the last hour.\n"
                    f"You're approaching Gmail limits!"
                )
        except Exception as e:
            logger.error(f"[Notifier] _check_rate_limit_warnings error: {e}")
        finally:
            if conn:
                conn.close()

    # ── Helpers ───────────────────────────────────────────────────

    def _maybe_first_time_milestone(self, key: str, company: str):
        """Fire a first-time milestone exactly once."""
        if key in self._milestones_fired:
            return
        emoji, label = FIRST_TIME_MILESTONES.get(key, ("✨", key))
        self._send_alert(
            f"{emoji} *{label}*\n\nCompany: *{company}*\nThis is a BIG moment! 🎊"
        )
        self._milestones_fired.add(key)

    def _status_emoji(self, status: str) -> str:
        return {
            "positive": "🟢",
            "interested": "🟢",
            "interview": "🎯",
            "offer": "🏆",
            "rejected": "🔴",
            "pending": "🟡",
            "viewed": "👀",
            "no_response": "⚪",
            "applied": "📨",
            "sent": "📨",
        }.get(status.lower(), "📌")

    @staticmethod
    def format_job_match_card(job: dict) -> str:
        """
        Format a job match into a rich Telegram alert card ($0 cost notification).
        """
        title = job.get("title") or job.get("job_title") or "Position"
        company = job.get("company") or job.get("company_name") or "Company"
        location = job.get("location") or "Remote"
        salary = job.get("salary") or job.get("salary_range") or "Competitive"
        url = job.get("url") or job.get("apply_url") or "https://jobhuntpro.app"
        match_score = job.get("match_score") or job.get("score") or "95%"

        return (
            f"🎯 *NEW HIGH-MATCH JOB DISCOVERED!*\n\n"
            f"💼 *Title:* {title}\n"
            f"🏢 *Company:* {company}\n"
            f"📍 *Location:* {location}\n"
            f"💰 *Salary:* {salary}\n"
            f"🔥 *AI Match Score:* {match_score}\n\n"
            f"🔗 [Apply Now Directly]({url})\n\n"
            f"_Powered by JobHunt Pro 24/7 AI Engine_"
        )

    def _send_alert(self, message: str):
        """Send alert via the async callback (runs in new event loop)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_callback(message))
            loop.close()
        except Exception as e:
            logger.error(f"[Notifier] Send failed: {e}")

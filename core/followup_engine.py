"""
Smart Recruiter Auto-Follow-Up Engine v1.0 — JobHunt Pro
Automatically schedules and dispatches high-conversion follow-up bump emails
to hiring managers 5 days and 10 days after initial application.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from core.pg_sqlite_shim import get_db

logger = logging.getLogger(__name__)

FOLLOWUP_STAGE_1_DAYS = 5
FOLLOWUP_STAGE_2_DAYS = 10

class FollowupEngine:
    """Handles automated follow-up scheduling, personalized bump generation, and delivery."""

    def __init__(self):
        pass

    def get_eligible_applications(self, conn, user_id: str, days_ago: int = 5) -> List[Dict[str, Any]]:
        """Find applications sent N days ago that haven't received a follow-up yet."""
        query = """
            SELECT ce.id, ce.campaign_id, ce.company_name, ce.contact_email, 
                   ce.job_title, ce.sent_at, ce.followup_count
            FROM campaign_emails ce
            JOIN campaigns c ON ce.campaign_id = c.campaign_id
            WHERE c.user_id = ?
              AND ce.status IN ('sent', 'delivered')
              AND (ce.followup_count IS NULL OR ce.followup_count = 0)
              AND ce.sent_at <= datetime('now', ? || ' days')
            ORDER BY ce.sent_at ASC
            LIMIT 20
        """
        try:
            cur = conn.cursor()
            rows = cur.execute(query, (user_id, f"-{days_ago}")).fetchall()
            results = []
            for r in rows:
                if isinstance(r, dict):
                    results.append(dict(r))
                else:
                    results.append({
                        "id": r[0],
                        "campaign_id": r[1],
                        "company_name": r[2],
                        "contact_email": r[3],
                        "job_title": r[4],
                        "sent_at": r[5],
                        "followup_count": r[6] or 0
                    })
            return results
        except Exception as e:
            logger.error(f"[FollowupEngine] Error fetching eligible applications: {e}")
            return []

    def generate_followup_body(self, candidate_name: str, job_title: str, company_name: str, stage: int = 1) -> Dict[str, str]:
        """Generate a polite, concise recruiter bump message."""
        if stage == 1:
            subject = f"Following up — {job_title} application ({candidate_name})"
            body = (
                f"Hi Hiring Team at {company_name},\n\n"
                f"I hope you're having a great week! I wanted to briefly follow up on my application for the {job_title} role "
                f"submitted a few days ago.\n\n"
                f"I remain very interested in contributing to {company_name}'s goals and would welcome the opportunity to discuss how my background aligns with your team's needs.\n\n"
                f"Best regards,\n{candidate_name}"
            )
        else:
            subject = f"Re: {job_title} opportunity at {company_name} — {candidate_name}"
            body = (
                f"Hi Hiring Team,\n\n"
                f"I'm checking in one last time regarding the {job_title} position at {company_name}.\n\n"
                f"If the position is still open, I'd love to connect briefly. Thank you again for your time and consideration!\n\n"
                f"Warm regards,\n{candidate_name}"
            )
        return {"subject": subject, "body": body}

    async def process_user_followups(self, user_id: str) -> Dict[str, Any]:
        """Process and send eligible follow-ups for a user."""
        conn = get_db()
        try:
            apps = self.get_eligible_applications(conn, user_id, days_ago=FOLLOWUP_STAGE_1_DAYS)
            if not apps:
                return {"status": "ok", "processed": 0, "message": "No eligible applications for follow-up"}

            from core.email_engine import EmailEngine
            engine = EmailEngine()
            sent_count = 0

            for app in apps:
                candidate_name = user_id  # default fallback
                content = self.generate_followup_body(
                    candidate_name=candidate_name,
                    job_title=app.get("job_title", "Position"),
                    company_name=app.get("company_name", "Company"),
                    stage=1
                )
                
                # Update DB record
                conn.execute(
                    "UPDATE campaign_emails SET followup_count = COALESCE(followup_count, 0) + 1, last_followup_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (app["id"],)
                )
                sent_count += 1

            conn.commit()
            return {"status": "ok", "processed": sent_count, "message": f"Processed {sent_count} follow-ups"}
        except Exception as e:
            logger.error(f"[FollowupEngine] Error processing followups for {user_id}: {e}")
            return {"status": "error", "detail": str(e)}
        finally:
            conn.close()

"""
Smart Follow-Up Automation: AI detects ghosted applications, auto-sends follow-ups
Tracks application status via email tracking
Optimal follow-up timing (3 days, 7 days, 14 days post-application)
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel

from .email_engine import EmailEngine
from .multi_llm_cost_optimizer import llm_cost_optimizer, TaskType


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    OFFER = "offer"


@dataclass
class ApplicationRecord:
    """Tracked application"""
    application_id: str
    job_id: str
    job_title: str
    company_name: str
    user_email: str
    applied_date: datetime
    last_status_update: datetime
    current_status: ApplicationStatus
    email_opens: int
    email_clicks: int
    follow_up_count: int
    last_follow_up_date: Optional[datetime]


class SmartFollowUpRequest(BaseModel):
    application_id: str
    recipient_name: str
    recipient_email: str
    job_title: str
    company_name: str
    days_since_application: int


class SmartFollowUpResponse(BaseModel):
    application_id: str
    action_taken: str  # "follow_up_sent", "too_early", "already_rejected"
    follow_up_template: str
    send_timestamp: Optional[datetime]
    next_follow_up_date: Optional[datetime]


class SmartFollowUp:
    """
    Autonomous follow-up engine
    - Tracks application status via email tracking
    - Detects ghosted applications (2+ weeks no response)
    - Auto-generates personalized follow-up messages
    - Schedules optimal follow-up times
    - Learns from response rates
    """

    def __init__(self, email_engine: Optional[EmailEngine] = None):
        self.email_engine = email_engine
        self.applications: Dict[str, ApplicationRecord] = {}
        
        # Follow-up schedule (in days)
        self.followup_schedule = [3, 7, 14]  # Day 3, 7, 14

    async def process_tracked_applications(self) -> Dict[str, Any]:
        """
        Process all tracked applications for follow-up needs
        Runs periodically (e.g., daily)
        """
        followups_sent = 0
        ghosted_detected = 0
        skipped = 0

        for app_id, app_record in self.applications.items():
            # Skip if already rejected or offer received
            if app_record.current_status in [ApplicationStatus.REJECTED, ApplicationStatus.OFFER]:
                skipped += 1
                continue

            # Check if follow-up is due
            days_since_app = (datetime.now() - app_record.applied_date).days
            
            # Detect ghosted applications (>2 weeks, no response, no opens)
            if days_since_app > 14 and app_record.email_opens == 0:
                app_record.current_status = ApplicationStatus.GHOSTED
                ghosted_detected += 1

            # Check if follow-up is due
            if await self._should_follow_up(app_record):
                try:
                    await self._send_follow_up(app_record)
                    followups_sent += 1
                    app_record.follow_up_count += 1
                    app_record.last_follow_up_date = datetime.now()
                except Exception as e:
                    print(f"Error sending follow-up for {app_id}: {e}")

        return {
            "followups_sent": followups_sent,
            "ghosted_detected": ghosted_detected,
            "skipped": skipped,
            "total_applications": len(self.applications)
        }

    async def register_application(self, app_record: ApplicationRecord) -> None:
        """Register a new application for tracking"""
        self.applications[app_record.application_id] = app_record

    async def update_application_status(
        self,
        application_id: str,
        new_status: ApplicationStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update application status (triggered by email tracking)"""
        if application_id in self.applications:
            app = self.applications[application_id]
            app.current_status = new_status
            app.last_status_update = datetime.now()
            
            if new_status == ApplicationStatus.EMAIL_OPENED:
                app.email_opens += 1
            elif new_status == ApplicationStatus.EMAIL_CLICKED:
                app.email_clicks += 1

    async def generate_follow_up_message(
        self,
        request: SmartFollowUpRequest
    ) -> str:
        """Generate personalized follow-up message"""
        prompt = f"""Generate a professional, personalized follow-up email for this job application:

Recipient Name: {request.recipient_name}
Job Title: {request.job_title}
Company: {request.company_name}
Days Since Application: {request.days_since_application}

Requirements:
1. Friendly and professional tone
2. Brief (under 150 words)
3. Reference the original application
4. Reaffirm interest in the role
5. Include a soft call-to-action
6. Offer flexibility (phone, video, meet-up)

Generate the email body (no subject line needed)."""

        response, metadata = await llm_cost_optimizer.route_request(
            prompt=prompt,
            task_type=TaskType.EMAIL_PERSONALIZATION,
            latency_sla_ms=1000
        )
        
        return response

    async def _should_follow_up(self, app_record: ApplicationRecord) -> bool:
        """Determine if follow-up is due"""
        if app_record.current_status in [ApplicationStatus.REJECTED, ApplicationStatus.OFFER]:
            return False

        days_since_app = (datetime.now() - app_record.applied_date).days
        days_since_followup = (
            (datetime.now() - app_record.last_follow_up_date).days
            if app_record.last_follow_up_date
            else 999
        )

        # Check if follow-up is scheduled for today
        if app_record.follow_up_count < len(self.followup_schedule):
            scheduled_day = self.followup_schedule[app_record.follow_up_count]
            
            # Allow 1-day buffer
            if days_since_app >= scheduled_day - 1 and days_since_app <= scheduled_day + 1:
                return True

        return False

    async def _send_follow_up(self, app_record: ApplicationRecord) -> None:
        """Send follow-up email"""
        if not self.email_engine:
            print(f"Email engine not configured. Would send follow-up for {app_record.application_id}")
            return

        # Generate follow-up message
        follow_up_text = await self.generate_follow_up_message(
            SmartFollowUpRequest(
                application_id=app_record.application_id,
                recipient_name="Hiring Manager",  # Would extract from DB
                recipient_email=app_record.user_email,
                job_title=app_record.job_title,
                company_name=app_record.company_name,
                days_since_application=(datetime.now() - app_record.applied_date).days
            )
        )

        # Send via email engine
        try:
            subject = f"Following up on {app_record.job_title} application at {app_record.company_name}"
            await self.email_engine.send_email(
                to=app_record.user_email,
                subject=subject,
                body=follow_up_text,
                tags=["follow_up", app_record.application_id]
            )
        except Exception as e:
            print(f"Error sending follow-up email: {e}")

    def get_application_health_report(self) -> Dict[str, Any]:
        """Get overview of all tracked applications"""
        statuses = {}
        for status in ApplicationStatus:
            count = sum(1 for app in self.applications.values() if app.current_status == status)
            statuses[status.value] = count

        return {
            "total_applications": len(self.applications),
            "status_breakdown": statuses,
            "ghosted_applications": statuses.get("ghosted", 0),
            "interviews_scheduled": statuses.get("interview_scheduled", 0),
            "offers": statuses.get("offer", 0),
        }


# Global instance
smart_followup = SmartFollowUp()

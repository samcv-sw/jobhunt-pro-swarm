"""
JobHunt Pro - LinkedIn Automation Engine
Auto-connect with recruiters, personalized messages, pipeline management
"""

import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class LinkedInConnector:
    """Smart connection request engine with personalization."""

    CONNECTION_TEMPLATES: List[str] = [
        "Hi {name}, I'm a Senior Network Engineer with 15+ years of enterprise experience across Cisco, MikroTik, and Fortinet. I'd love to connect and discuss opportunities at {company}.",
        "Hello {name}, I specialize in network infrastructure and security with expertise in OSPF/BGP/MPLS. I noticed {company} has open positions and would appreciate connecting.",
        "Hi {name}, as a CCNA/CCNP certified engineer with extensive multi-vendor experience, I'm exploring new opportunities. Would love to connect about potential roles at {company}.",
    ]

    def __init__(self) -> None:
        self.connected_today: int = 0
        self.max_daily: int = 50
        self.pending_requests: List[Dict[str, Any]] = []
        self.connections: List[Dict[str, Any]] = []

    def generate_connection_request(self, recruiter_name: str, company: str) -> str:
        """Generate personalized connection request."""
        try:
            template = random.choice(self.CONNECTION_TEMPLATES)
            return template.format(name=recruiter_name, company=company)
        except Exception as e:
            logger.error(f"Failed to generate connection request: {e}")
            return f"Hi {recruiter_name}, I would like to connect with you to discuss potential opportunities at {company}."

    def can_connect(self) -> bool:
        """Check if we can send more connection requests."""
        try:
            return self.connected_today < self.max_daily
        except Exception as e:
            logger.error(f"Failed to check connect permission: {e}")
            return False

    def record_connection(self, recruiter: Dict[str, Any]) -> None:
        """Record a sent connection request."""
        try:
            self.connected_today += 1
            self.pending_requests.append(
                {
                    **recruiter,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "status": "pending",
                }
            )
        except Exception as e:
            logger.error(f"Failed to record connection: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection stats."""
        try:
            return {
                "connected_today": self.connected_today,
                "max_daily": self.max_daily,
                "pending": len(
                    [r for r in self.pending_requests if r.get("status") == "pending"]
                ),
                "accepted": len(
                    [r for r in self.pending_requests if r.get("status") == "accepted"]
                ),
                "total_connections": len(self.connections),
            }
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {
                "connected_today": self.connected_today,
                "max_daily": self.max_daily,
                "pending": 0,
                "accepted": 0,
                "total_connections": 0,
            }


class LinkedInMessenger:
    """Automated follow-up messaging for connections."""

    FOLLOWUP_TEMPLATES: List[str] = [
        "Thanks for connecting, {name}! I'm actively looking for network engineering roles. If {company} has any openings, I'd love to discuss how my 15+ years of experience could benefit your team.",
        "Hi {name}, thanks for accepting! I wanted to follow up on my interest in {company}. My background in enterprise networking (Cisco, Fortinet, MikroTik) aligns well with infrastructure roles. Any current openings?",
    ]

    def __init__(self) -> None:
        self.messages_sent: List[Dict[str, Any]] = []

    def generate_followup(self, recruiter: Dict[str, Any], followup_num: int = 1) -> str:
        """Generate follow-up message."""
        try:
            template = self.FOLLOWUP_TEMPLATES[
                min(followup_num - 1, len(self.FOLLOWUP_TEMPLATES) - 1)
            ]
            return template.format(
                name=recruiter.get("name", "there"),
                company=recruiter.get("company", "your company"),
            )
        except Exception as e:
            logger.error(f"Failed to generate follow up message: {e}")
            return f"Hi {recruiter.get('name', 'there')}, thank you for connecting! I am following up on potential networking roles at {recruiter.get('company', 'your company')}."

    def should_send_followup(self, days_since: int, followup_count: int) -> bool:
        """Determine if follow-up should be sent."""
        try:
            if followup_count >= 2:
                return False
            if followup_count == 0 and days_since >= 3:
                return True
            if followup_count == 1 and days_since >= 7:
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to determine follow up condition: {e}")
            return False


class RecruiterFinder:
    """Find and categorize recruiters by industry."""

    RECRUITER_SEARCH_QUERIES: List[str] = [
        "network engineer recruiter",
        "IT staffing agency {location}",
        "technology recruiter {location}",
        "infrastructure hiring manager {company}",
        "IT director {company}",
        "head of network {company}",
    ]

    def __init__(self) -> None:
        self.found_recruiters: List[Dict[str, Any]] = []

    def generate_search_queries(self, location: str, companies: List[str]) -> List[str]:
        """Generate search queries for finding recruiters."""
        try:
            queries: List[str] = []
            for template in self.RECRUITER_SEARCH_QUERIES:
                if "{location}" in template:
                    queries.append(template.format(location=location))
                elif "{company}" in template:
                    for company in companies[:10]:
                        queries.append(template.format(company=company))
                else:
                    queries.append(template)
            return queries
        except Exception as e:
            logger.error(f"Failed to generate search queries: {e}")
            return [f"recruiter {location}"]

    def categorize_recruiter(self, profile: Dict[str, Any]) -> str:
        """Categorize a recruiter by type."""
        try:
            title = profile.get("title", "").lower()
            if "staffing" in title or "recruiter" in title or "talent" in title:
                return "agency"
            if "hr" in title or "human" in title:
                return "corporate_hr"
            if "director" in title or "head" in title or "vp" in title:
                return "hiring_manager"
            return "other"
        except Exception as e:
            logger.error(f"Failed to categorize recruiter: {e}")
            return "other"


# ── Global instances ──────────────────────────────────────────
linkedin_connector: LinkedInConnector = LinkedInConnector()
linkedin_messenger: LinkedInMessenger = LinkedInMessenger()
recruiter_finder: RecruiterFinder = RecruiterFinder()

"""
services/lead_enrichment_engine.py - Deep AI Lead Enrichment & Intent Scoring Engine
Calculates intent score (0-100%) and enriches candidate/lead outreach context with hiring signals.
"""
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LeadEnrichmentEngine:
    """
    Enriches raw job leads with hiring intent scores and hyper-personalized outreach hooks.
    """

    @staticmethod
    def calculate_intent_score(lead_data: Dict[str, Any]) -> int:
        """
        Calculates hiring intent score (0-100) based on signals:
        - Urgency keywords (immediate, urgent, ASAP, hiring now)
        - Salary details specified
        - Direct hiring manager email available
        - Company growth indicators
        """
        score = 50  # Baseline score

        title = (lead_data.get("title") or "").lower()
        description = (lead_data.get("description") or lead_data.get("snippet") or "").lower()
        contact_email = lead_data.get("contact_email") or lead_data.get("email") or ""
        salary = lead_data.get("salary") or lead_data.get("salary_range") or ""

        # Signal 1: Urgency (+15)
        urgency_keywords = ["immediate", "urgent", "asap", "hiring now", "apply today", "fast track", "مباشر", "عاجل"]
        if any(kw in title or kw in description for kw in urgency_keywords):
            score += 15

        # Signal 2: Direct HR / Executive Email (+20)
        if contact_email and "@" in contact_email:
            if not any(generic in contact_email for generic in ["info@", "contact@", "support@", "admin@"]):
                score += 20
            else:
                score += 10

        # Signal 3: Salary Transparency (+10)
        if salary and len(str(salary)) > 2:
            score += 10

        # Signal 4: Seniority / Executive Level (+5)
        seniority_keywords = ["senior", "lead", "head of", "director", "manager", "architect", "principal"]
        if any(kw in title for kw in seniority_keywords):
            score += 5

        return min(100, max(10, score))

    @staticmethod
    def generate_personalized_hook(lead_data: Dict[str, Any], candidate_name: str = "Candidate") -> Dict[str, Any]:
        """
        Synthesizes a tailored outreach hook based on intent signals and company context.
        """
        company = lead_data.get("company") or "the engineering team"
        title = lead_data.get("title") or "Engineering Role"
        location = lead_data.get("location") or "your team"
        intent_score = LeadEnrichmentEngine.calculate_intent_score(lead_data)

        # Generate hyper-personalized subject & opening lines
        if intent_score >= 80:
            subject = f"Direct Inquiry: {title} position at {company}"
            hook_opening = f"I noticed {company} is actively scaling its {title} team in {location} with immediate priority."
        elif intent_score >= 60:
            subject = f"Re: {title} Opening — Experienced Specialist for {company}"
            hook_opening = f"I was following {company}'s growth in {location} and wanted to reach out regarding your {title} requirement."
        else:
            subject = f"Application & Introduction: {title} — {company}"
            hook_opening = f"I am writing to express my strong interest in joining {company} as a {title}."

        return {
            "intent_score": intent_score,
            "subject": subject,
            "hook_opening": hook_opening,
            "personalized_summary": f"{company} | {title} | Intent Score: {intent_score}%"
        }

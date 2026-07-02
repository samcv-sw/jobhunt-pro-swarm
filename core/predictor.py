"""
RESPONSE PREDICTION SYSTEM
Ported from Rita Project - Predict likelihood of response before sending
"""

import logging
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Historical data file
HISTORY_FILE = Path("cache/response_history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# Minimum confidence threshold to send (0-100)
MIN_CONFIDENCE_THRESHOLD = int(os.getenv("MIN_RESPONSE_CONFIDENCE", "50"))


class ResponsePredictor:
    """Predict likelihood of email response using ML-like scoring."""

    def __init__(self):
        self.history = self._load_history()
        # O(1) company lookup index: company_lower -> last known responded bool
        self._company_index: Dict[str, bool] = {
            rec.get("company", "").lower().strip(): rec.get("responded", False)
            for rec in self.history.get("emails", [])
        }

    def _load_history(self) -> Dict:
        """Load historical response data"""
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, "r") as f:
                    return json.load(f)
            return {"emails": [], "patterns": {}}
        except Exception as e:
            logger.warning(f"Failed to load response history: {e}")
            return {"emails": [], "patterns": {}}

    def _save_history(self):
        """Save response history"""
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save response history: {e}")

    def analyze_email_quality(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email quality factors"""
        scores = {}

        # Subject line analysis
        subject_len = len(subject)
        # More lenient: 30-80 chars is good for compelling subject lines with certifications
        scores["subject_length"] = (
            100
            if 30 <= subject_len <= 80
            else max(0, 100 - abs(55 - subject_len) * 1.5)
        )

        # Check for personalization in subject - also check for certifications/experience indicators
        subject_lower = subject.lower()
        has_personalization = any(
            word in subject_lower
            for word in ["your", "you", "re:", "available", "experienced"]
        )
        has_certifications = any(
            word in subject_lower
            for word in [
                "ccnp",
                "nse",
                "aws",
                "ccie",
                "expert",
                "senior",
                "15yr",
                "specialist",
            ]
        )
        scores["subject_personalized"] = (
            100 if (has_personalization or has_certifications) else 50
        )

        # Body length analysis (optimal: 150-300 words for detailed cover letters)
        word_count = len(body.split())
        scores["body_length"] = (
            100
            if 150 <= word_count <= 300
            else max(0, 100 - abs(225 - word_count) * 0.4)
        )

        # Check for numbers/metrics - critical for engineering roles
        has_numbers = bool(re.search(r"\d+", body))
        has_percentages = bool(re.search(r"\d+%", body))
        scores["has_metrics"] = 100 if has_percentages else (80 if has_numbers else 30)

        # Check for relevant technical keywords in body
        tech_keywords = [
            "sd-wan",
            "network",
            "security",
            "cloud",
            "automation",
            "infrastructure",
            "zero trust",
            "mpls",
            "bgp",
            "firewall",
            "data center",
            "ansible",
            "terraform",
            "python",
            "cisco",
            "fortinet",
            "aws",
            "azure",
        ]
        tech_match_count = sum(1 for kw in tech_keywords if kw in body.lower())
        scores["technical_relevance"] = min(
            100, tech_match_count * 15
        )  # Up to 100 for 7+ matches

        # Safety check: Detect raw/unresolved template placeholders (failed template replacement)
        unresolved_placeholders = [
            "{first_name}",
            "{company}",
            "{position}",
            "{title}",
            "{company_name}",
            "[Company Name]",
            "[Recruiter Name]",
            "[Job Title]",
            "[Insert",
            "<first_name>",
            "<company>",
            "<position>",
        ]
        has_unresolved = any(
            placeholder.lower() in body.lower()
            or placeholder.lower() in subject.lower()
            for placeholder in unresolved_placeholders
        )
        has_empty_braces = bool(re.search(r"\{\s*\}|\[\s*\]|<\s*>", body + subject))

        if has_unresolved or has_empty_braces:
            # Personalization is a complete failure if raw braces/tags leak into the final output
            scores["personalization"] = 0
            scores["unresolved_gate"] = 0  # 0 denotes a critical failure gate
        else:
            # Good personalization check: check if it features the candidate's name or is custom-tailored
            has_candidate_name = "sam" in body.lower() or "salameh" in body.lower()
            scores["personalization"] = 100 if has_candidate_name else 70

        # Check for call to action
        cta_words = [
            "schedule",
            "call",
            "discuss",
            "meeting",
            "available",
            "apply",
            "interview",
            "conversation",
        ]
        has_cta = any(word in body.lower() for word in cta_words)
        scores["call_to_action"] = 100 if has_cta else 40

        # Check for urgency
        urgency_words = [
            "asap",
            "urgent",
            "immediate",
            "deadline",
            "opportunity",
            "available",
        ]
        has_urgency = any(word in body.lower() for word in urgency_words)
        scores["urgency"] = 100 if has_urgency else 60

        return scores

    def analyze_company_responsiveness(self, company: str) -> float:
        """Analyze company responsiveness based on history — O(1) index lookup."""
        default_responsiveness = 50
        company_lower = company.lower().strip()
        if company_lower in self._company_index:
            return 80 if self._company_index[company_lower] else 30
        return default_responsiveness

    def predict_response_rate(
        self, subject: str, body: str, company: str = ""
    ) -> Dict[str, Any]:
        """Predict response rate for an email"""
        # Analyze email quality
        quality_scores = self.analyze_email_quality(subject, body)

        # Calculate quality average excluding the safety gate key
        scoring_keys = [k for k in quality_scores.keys() if k != "unresolved_gate"]
        quality_avg = sum(quality_scores[k] for k in scoring_keys) / len(scoring_keys)

        # Analyze company responsiveness
        company_responsiveness = self.analyze_company_responsiveness(company)

        # Calculate overall confidence
        confidence = quality_avg * 0.6 + company_responsiveness * 0.4
        confidence = min(confidence, 100)

        # safety gate check
        failed_gate = quality_scores.get("unresolved_gate", 100) == 0

        return {
            "confidence": 0.0 if failed_gate else round(confidence, 1),
            "quality_scores": {
                k: v for k, v in quality_scores.items() if k != "unresolved_gate"
            },
            "company_responsiveness": company_responsiveness,
            "should_send": False
            if failed_gate
            else (confidence >= MIN_CONFIDENCE_THRESHOLD),
            "reason": "CRITICAL: Unresolved template placeholders detected!"
            if failed_gate
            else self._get_send_reason(confidence, quality_scores),
        }

    def _get_send_reason(self, confidence: float, quality_scores: Dict) -> str:
        """Get reason for send/no-send decision"""
        if confidence >= 80:
            return "High confidence - excellent email quality"
        elif confidence >= 60:
            return "Moderate confidence - acceptable quality"
        elif confidence >= 40:
            return "Low confidence - consider improvements"
        else:
            return "Very low confidence - major improvements needed"

    def record_sent_email(
        self, company: str, email: str, subject: str, body: str, responded: bool = False
    ):
        """Record a sent email for future learning"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "company": company,
            "email": email,
            "subject": subject,
            "body": body[:200] + "..." if len(body) > 200 else body,
            "responded": responded,
            "quality_scores": self.analyze_email_quality(subject, body),
        }

        self.history["emails"].append(record)
        # Update O(1) index
        self._company_index[company.lower().strip()] = responded

        # Keep only last 1000 emails
        if len(self.history["emails"]) > 1000:
            self.history["emails"] = self.history["emails"][-1000:]

        self._save_history()
        logger.debug(f"Recorded email to {company}")

    def record_response(self, company: str, email: str):
        """Record that a company responded"""
        for record in reversed(self.history["emails"]):
            if (
                record.get("company", "").lower() == company.lower()
                and record.get("email", "").lower() == email.lower()
            ):
                record["responded"] = True
                record["responded_at"] = datetime.now().isoformat()
                # Update O(1) index
                self._company_index[company.lower().strip()] = True
                self._save_history()
                logger.info(f"Recorded response from {company}")
                return

        logger.warning(f"No email record found for {company}/{email}")

    def get_stats(self) -> Dict:
        """Get prediction statistics"""
        emails = self.history.get("emails", [])
        responses = [e for e in emails if e.get("responded")]

        return {
            "total_emails": len(emails),
            "total_responses": len(responses),
            "response_rate": len(responses) / len(emails) * 100 if emails else 0,
            "avg_confidence": sum(
                e.get("quality_scores", {}).get("overall", 0) for e in emails
            )
            / len(emails)
            if emails
            else 0,
        }


# Global instance
predictor = ResponsePredictor()

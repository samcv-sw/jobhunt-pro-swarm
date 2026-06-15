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
from typing import Dict, Any, Optional, List

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
    
    def _load_history(self) -> Dict:
        """Load historical response data"""
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            return {"emails": [], "patterns": {}}
        except Exception as e:
            logger.warning(f"Failed to load response history: {e}")
            return {"emails": [], "patterns": {}}
    
    def _save_history(self):
        """Save response history"""
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save response history: {e}")
    
    def analyze_email_quality(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email quality factors"""
        scores = {}
        
        # Subject line analysis
        subject_len = len(subject)
        scores["subject_length"] = 100 if 40 <= subject_len <= 60 else max(0, 100 - abs(50 - subject_len) * 2)
        
        # Check for personalization in subject
        scores["subject_personalized"] = 100 if any(word in subject.lower() for word in ['your', 'you', 're:']) else 50
        
        # Body length analysis (optimal: 150-250 words)
        word_count = len(body.split())
        scores["body_length"] = 100 if 150 <= word_count <= 250 else max(0, 100 - abs(200 - word_count) * 0.5)
        
        # Check for numbers/metrics
        has_numbers = bool(re.search(r'\d+', body))
        scores["has_metrics"] = 100 if has_numbers else 30
        
        # Check for personalization tokens
        personalization_tokens = ['{first_name}', '{company}', '{position}']
        has_tokens = any(token in body for token in personalization_tokens)
        scores["personalization"] = 100 if has_tokens else 50
        
        # Check for call to action
        cta_words = ['schedule', 'call', 'discuss', 'meeting', 'available', 'apply']
        has_cta = any(word in body.lower() for word in cta_words)
        scores["call_to_action"] = 100 if has_cta else 40
        
        # Check for urgency
        urgency_words = ['asap', 'urgent', 'immediate', 'deadline']
        has_urgency = any(word in body.lower() for word in urgency_words)
        scores["urgency"] = 100 if has_urgency else 60
        
        return scores
    
    def analyze_company_responsiveness(self, company: str) -> float:
        """Analyze company responsiveness based on history"""
        # Default responsiveness
        default_responsiveness = 50
        
        # Check if we have history for this company
        company_lower = company.lower().strip()
        
        for email in self.history.get("emails", []):
            if email.get("company", "").lower().strip() == company_lower:
                # Calculate response rate
                responses = email.get("responded", False)
                return 80 if responses else 30
        
        return default_responsiveness
    
    def predict_response_rate(self, subject: str, body: str, company: str = "") -> Dict[str, Any]:
        """Predict response rate for an email"""
        # Analyze email quality
        quality_scores = self.analyze_email_quality(subject, body)
        quality_avg = sum(quality_scores.values()) / len(quality_scores)
        
        # Analyze company responsiveness
        company_responsiveness = self.analyze_company_responsiveness(company)
        
        # Calculate overall confidence
        confidence = (quality_avg * 0.6 + company_responsiveness * 0.4)
        
        # Cap at 100
        confidence = min(confidence, 100)
        
        return {
            "confidence": round(confidence, 1),
            "quality_scores": quality_scores,
            "company_responsiveness": company_responsiveness,
            "should_send": confidence >= MIN_CONFIDENCE_THRESHOLD,
            "reason": self._get_send_reason(confidence, quality_scores)
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
    
    def record_sent_email(self, company: str, email: str, subject: str, body: str, 
                          responded: bool = False):
        """Record a sent email for future learning"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "company": company,
            "email": email,
            "subject": subject,
            "body": body[:200] + "..." if len(body) > 200 else body,
            "responded": responded,
            "quality_scores": self.analyze_email_quality(subject, body)
        }
        
        self.history["emails"].append(record)
        
        # Keep only last 1000 emails
        if len(self.history["emails"]) > 1000:
            self.history["emails"] = self.history["emails"][-1000:]
        
        self._save_history()
        logger.debug(f"Recorded email to {company}")
    
    def record_response(self, company: str, email: str):
        """Record that a company responded"""
        for record in reversed(self.history["emails"]):
            if record.get("company", "").lower() == company.lower() and \
               record.get("email", "").lower() == email.lower():
                record["responded"] = True
                record["responded_at"] = datetime.now().isoformat()
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
            "avg_confidence": sum(e.get("quality_scores", {}).get("overall", 0) for e in emails) / len(emails) if emails else 0
        }


# Global instance
predictor = ResponsePredictor()

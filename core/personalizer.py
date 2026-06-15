"""
EMAIL PERSONALIZATION SYSTEM
Ported from Rita Project - Dynamic content for better response rates
"""

import logging
import os
import json
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class EmailPersonalizer:
    """Advanced email personalization with dynamic tokens."""
    
    def __init__(self):
        self.candidate_data = self._load_candidate_data()
        self.company_data = {}
    
    def _load_candidate_data(self) -> Dict[str, Any]:
        """Load candidate's data from environment."""
        return {
            "name": os.getenv("CANDIDATE_NAME", "Sam Salameh"),
            "phone": os.getenv("CANDIDATE_PHONE", "+961 71 019 053"),
            "email": os.getenv("SENDER_EMAIL", "samatou683@gmail.com"),
            "linkedin": os.getenv("LINKEDIN_URL", "https://www.linkedin.com/in/sam-salameh"),
            "profession": os.getenv("CANDIDATE_PROFESSION", "Senior Network Engineer"),
            
            "achievements": [
                "40% efficiency improvement",
                "$2M cost savings",
                "15-person team management",
                "Zero downtime deployment",
                "300+ successful implementations"
            ],
            
            "skills": [
                "Network Engineering",
                "Team Leadership",
                "Process Optimization",
                "Cost Reduction",
                "Infrastructure Management"
            ],
            
            "industries": [
                "Technology",
                "Telecommunications",
                "Enterprise IT"
            ]
        }
    
    def extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name"""
        if not full_name:
            return ""
        
        # Remove common prefixes
        name = re.sub(r'^(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s*', '', full_name, flags=re.IGNORECASE)
        
        # Get first part
        parts = name.strip().split()
        if parts:
            return parts[0]
        return ""
    
    def personalize_token(self, token: str, company_info: Dict = None) -> str:
        """Replace a token with personalized content"""
        if not company_info:
            company_info = {}
        
        token_map = {
            "{first_name}": self.extract_first_name(company_info.get("contact_name", "")),
            "{company}": company_info.get("company", "your company"),
            "{position}": company_info.get("title", "the position"),
            "{relevant_skill}": self._get_relevant_skill(company_info),
            "{achievement}": self._get_relevant_achievement(company_info),
            "{pain_point}": self._get_pain_point(company_info),
            "{candidate_name}": self.candidate_data["name"],
            "{candidate_email}": self.candidate_data["email"],
            "{candidate_phone}": self.candidate_data["phone"],
            "{candidate_profession}": self.candidate_data["profession"],
        }
        
        return token_map.get(token, token)
    
    def personalize_email(self, template: str, company_info: Dict = None) -> str:
        """Personalize an email template with dynamic content"""
        if not company_info:
            company_info = {}
        
        result = template
        
        # Replace all tokens
        for token in ["{first_name}", "{company}", "{position}", 
                      "{relevant_skill}", "{achievement}", "{pain_point}",
                      "{candidate_name}", "{candidate_email}", 
                      "{candidate_phone}", "{candidate_profession}"]:
            replacement = self.personalize_token(token, company_info)
            result = result.replace(token, replacement)
        
        return result
    
    def _get_relevant_skill(self, company_info: Dict) -> str:
        """Get a relevant skill based on company/position"""
        industry = company_info.get("industry", "").lower()
        
        if "telecom" in industry or "network" in industry:
            return "network infrastructure optimization"
        elif "security" in industry:
            return "cybersecurity implementation"
        elif "cloud" in industry:
            return "cloud migration and management"
        else:
            return "process optimization and cost reduction"
    
    def _get_relevant_achievement(self, company_info: Dict) -> str:
        """Get a relevant achievement based on company"""
        return "reducing operational costs by 40% while improving system reliability"
    
    def _get_pain_point(self, company_info: Dict) -> str:
        """Identify potential pain point for the company"""
        industry = company_info.get("industry", "").lower()
        
        if "telecom" in industry:
            return "network downtime and performance issues"
        elif "security" in industry:
            return "security vulnerabilities and compliance challenges"
        else:
            return "operational inefficiencies and rising costs"
    
    def generate_subject_variants(self, base_subject: str, company: str) -> List[str]:
        """Generate multiple subject line variants for A/B testing"""
        variants = [
            base_subject,
            f"Re: {base_subject}",
            f"Quick question about {company}",
            f"{self.candidate_data['name']} - {base_subject}",
            f"Interested in {company}",
        ]
        return variants
    
    def analyze_email_quality(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email quality factors"""
        scores = {}
        
        # Subject length (optimal: 40-60 chars)
        subject_len = len(subject)
        scores["subject_length"] = 100 if 40 <= subject_len <= 60 else max(0, 100 - abs(50 - subject_len) * 2)
        
        # Body length (optimal: 150-250 words)
        word_count = len(body.split())
        scores["body_length"] = 100 if 150 <= word_count <= 250 else max(0, 100 - abs(200 - word_count) * 0.5)
        
        # Personalization check
        has_name = any(word in body.lower() for word in ['dear', 'hello', 'hi'])
        scores["personalization"] = 100 if has_name else 50
        
        # Numbers/metrics
        has_numbers = bool(re.search(r'\d+', body))
        scores["has_metrics"] = 100 if has_numbers else 30
        
        # Call to action
        cta_words = ['schedule', 'call', 'discuss', 'meeting', 'available']
        has_cta = any(word in body.lower() for word in cta_words)
        scores["call_to_action"] = 100 if has_cta else 40
        
        # Overall score
        scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores


# Global instance
personalizer = EmailPersonalizer()

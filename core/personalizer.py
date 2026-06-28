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

# Precompile prefix regex globally to improve name parsing performance
PREFIX_RE = re.compile(r'^(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s*', re.IGNORECASE)


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
            "email": os.getenv("SENDER_EMAIL", "samsalameh.cv@gmail.com"),
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
        
        # Remove common prefixes using globally precompiled regex
        name = PREFIX_RE.sub('', full_name)
        
        # Get first part
        parts = name.strip().split()
        if parts:
            return parts[0]
        return ""
    
    def personalize_token(self, token: str, company_info: Dict = None) -> str:
        """Replace a token with personalized content"""
        if not company_info:
            company_info = {}
        
        contact_name = company_info.get("contact_name", "")
        first_name = self.extract_first_name(contact_name)
        if not first_name or not first_name.strip():
            first_name = "Hiring Manager"
        
        token_map = {
            "{first_name}": first_name,
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
        """Personalize an email template with dynamic content in a single pass."""
        if not company_info:
            company_info = {}
        
        contact_name = company_info.get("contact_name", "")
        first_name = self.extract_first_name(contact_name)
        if not first_name or not first_name.strip():
            first_name = "Hiring Manager"
        
        # Build token map once per email to prevent redundant computations
        token_map = {
            "{first_name}": first_name,
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
        
        result = template
        for token, replacement in token_map.items():
            if token in result:
                result = result.replace(token, replacement)
        
        return result
    
    def _get_relevant_skill(self, company_info: Dict) -> str:
        """Get a relevant skill based on company/position"""
        industry = company_info.get("industry", "").lower()
        title = company_info.get("title", "").lower()
        
        if "sd-wan" in title or "sase" in title:
            return "SD-WAN and SASE architecture design and deployment"
        elif "security" in industry or "security" in title or "soc" in title:
            return "network security, Zero Trust architecture, and NGFW implementation"
        elif "cloud" in industry or "cloud" in title:
            return "multi-cloud networking (AWS/Azure/GCP) and hybrid cloud architecture"
        elif "automation" in title or "devops" in title:
            return "network automation with Python, Ansible, and Terraform"
        elif "telecom" in industry or "telecom" in title or "isp" in title:
            return "large-scale ISP/MPLS network design and optimization"
        elif "data center" in title or "dc" in title:
            return "data center network architecture with VXLAN/EVPN and ACI"
        elif "network" in industry or "network" in title:
            return "enterprise network infrastructure design and optimization"
        elif "solutions" in title or "architect" in title:
            return "end-to-end network solutions architecture and digital transformation"
        else:
            return "network infrastructure optimization and cost reduction"
    
    def _get_relevant_achievement(self, company_info: Dict) -> str:
        """Get a relevant achievement based on company"""
        title = company_info.get("title", "").lower()
        
        if "sd-wan" in title or "sase" in title:
            return "architecting SD-WAN solutions across 50+ sites, reducing WAN costs by 45%"
        elif "security" in title or "soc" in title:
            return "implementing Zero Trust security for 2,000+ users across 10+ countries"
        elif "cloud" in title:
            return "migrating 100+ servers to cloud with 99.99% uptime and 40% cost reduction"
        elif "automation" in title or "devops" in title:
            return "automating network operations with Python/Ansible, reducing deployment time by 40%"
        elif "data center" in title:
            return "designing Tier III data center networks supporting 500+ critical workloads"
        elif "architect" in title or "solutions" in title:
            return "managing $5M+ infrastructure budgets and leading 12-person engineering teams"
        elif "manager" in title or "director" in title or "head" in title:
            return "leading cross-functional teams of 12 engineers, managing $5M+ annual budgets"
        else:
            return "reducing operational costs by 45% while improving network reliability to 99.99%"
    
    def _get_pain_point(self, company_info: Dict) -> str:
        """Identify potential pain point for the company"""
        industry = company_info.get("industry", "").lower()
        title = company_info.get("title", "").lower()
        
        if "sd-wan" in title or "sase" in title:
            return "legacy MPLS costs and complex branch connectivity challenges"
        elif "security" in industry or "security" in title:
            return "evolving cyber threats, Zero Trust adoption, and compliance requirements"
        elif "cloud" in industry or "cloud" in title:
            return "cloud migration complexity, hybrid connectivity, and multi-cloud management"
        elif "telecom" in industry or "isp" in industry:
            return "network scalability, service availability, and rising operational costs"
        elif "automation" in title or "devops" in title:
            return "manual network operations slowing down business agility and digital transformation"
        elif "data center" in title:
            return "data center modernization, network virtualization, and capacity planning"
        elif "bank" in industry or "finance" in industry:
            return "regulatory compliance, network security, and business continuity requirements"
        else:
            return "network complexity, operational inefficiencies, and digital transformation challenges"
    
    def generate_subject_variants(self, base_subject: str, company: str) -> List[str]:
        """Generate multiple subject line variants for A/B testing"""
        name = self.candidate_data['name']
        variants = [
            base_subject,
            f"Re: {base_subject}",
            f"Quick question about {company}",
            f"{name} - {base_subject}",
            f"Interested in {company}",
            # More compelling variants
            f"{name} | 15yr Network Engineer | CCNP/NSE/AWS",
            f"Experienced Network Engineer for {company}",
            f"SD-WAN & Security Expert | {name}",
            f"Network Infrastructure Specialist - {name}",
            f"Available: Senior Network Engineer (CCNP, NSE, AWS)",
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

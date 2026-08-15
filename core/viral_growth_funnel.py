"""
core/viral_growth_funnel.py
============================
Viral ATS Growth Funnel & Resume Penetration Scoring Engine.
Provides instant ATS parsing, keyword gap detection, and viral referral loops
with token multipliers to drive zero-CAC user acquisition.
"""

import hashlib
import logging
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

logger = logging.getLogger("ViralGrowthFunnel")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

CORE_TECH_KEYWORDS = {
    "python", "fastapi", "docker", "kubernetes", "sql", "postgresql", "aws", "gcp",
    "react", "typescript", "nextjs", "redis", "ci/cd", "git", "rest api", "graphql",
    "microservices", "agile", "scrum", "leadership", "optimization", "security"
}


class ViralGrowthFunnel:
    """
    Analyzes resumes against modern ATS filters and manages viral referral links.
    """

    @staticmethod
    def analyze_resume_ats_score(resume_text: str, job_description: str = "") -> Dict[str, Any]:
        """
        Calculates an ATS pass score (0-100), detects keyword density, and returns improvement recommendations.
        """
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "ats_score": 35,
                "rating": "Needs Improvement",
                "matched_keywords": [],
                "missing_keywords": list(CORE_TECH_KEYWORDS)[:6],
                "recommendations": ["Expand your resume with measurable metrics and modern tech stack keywords."],
            }

        resume_lower = resume_text.lower()
        
        # Determine target keywords
        target_keywords = set(CORE_TECH_KEYWORDS)
        if job_description:
            # Extract common technical words from JD
            jd_words = re.findall(r"\b[a-zA-Z]{3,15}\b", job_description.lower())
            custom_targets = {w for w in jd_words if w in CORE_TECH_KEYWORDS or len(w) > 5}
            if custom_targets:
                target_keywords = target_keywords.union(custom_targets)

        matched: List[str] = [kw for kw in target_keywords if kw in resume_lower]
        missing: List[str] = [kw for kw in target_keywords if kw not in resume_lower]

        # Scoring heuristics
        # 4+ core tech keywords is solid density for a summary
        tech_density_score = min(40, len(matched) * 8)
        has_metrics = bool(re.search(r"\b\d+[%+kKmM]?\b", resume_text))
        has_action_verbs = any(v in resume_lower for v in ["built", "designed", "engineered", "led", "optimized", "increased", "developed", "managed"])

        score = tech_density_score
        if has_metrics:
            score += 25
        if has_action_verbs:
            score += 20
        if len(resume_text.split()) > 10:
            score += 10

        final_score = min(98, max(35, score))

        recommendations = []
        if not has_metrics:
            recommendations.append("Add quantifiable achievements (e.g. 'Increased speed by 40%').")
        if missing:
            recommendations.append(f"Consider including key skills: {', '.join(missing[:5])}.")
        if final_score >= 85:
            recommendations.append("Strong ATS optimization! Your resume is ready for automated dispatch.")

        return {
            "ats_score": final_score,
            "rating": "Excellent" if final_score >= 85 else "Good" if final_score >= 70 else "Needs Tailoring",
            "matched_keywords": matched[:12],
            "missing_keywords": missing[:8],
            "recommendations": recommendations,
        }

    @staticmethod
    def generate_referral_code(user_id: str) -> str:
        """Generates a short, unique viral referral code for a user."""
        return hashlib.md5(f"ref:{user_id}".encode("utf-8")).hexdigest()[:8].upper()

    @staticmethod
    def generate_viral_share_links(referral_code: str, base_url: str = "https://jobhuntpro.io") -> Dict[str, str]:
        """
        Creates one-click viral sharing links with tracking UTMs.
        """
        ref_url = f"{base_url.rstrip('/')}/signup?ref={referral_code}"
        share_text = (
            "I automated my entire job search with JobHunt Pro SaaS! "
            "Get free CV tailoring and automated ATS job applications here:"
        )
        encoded_text = urllib.parse.quote(f"{share_text} {ref_url}")
        encoded_url = urllib.parse.quote(ref_url)

        return {
            "referral_url": ref_url,
            "whatsapp": f"https://api.whatsapp.com/send?text={encoded_text}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
            "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}",
            "telegram": f"https://t.me/share/url?url={encoded_url}&text={urllib.parse.quote(share_text)}",
        }


# Global singleton
viral_funnel = ViralGrowthFunnel()

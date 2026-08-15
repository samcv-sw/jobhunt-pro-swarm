"""
ATS Smart Tailor & Real-Time Keyword Optimizer
Analyzes target job descriptions, computes exact keyword overlap,
and generates optimized CV summaries & bullet points matching ATS standards.
"""

import re
from typing import Dict, Any, List, Set

COMMON_TECH_SKILLS = [
    "python", "fastapi", "django", "flask", "postgresql", "sqlite", "redis",
    "docker", "kubernetes", "aws", "gcp", "azure", "graphql", "rest api",
    "next.js", "react", "typescript", "javascript", "tailwind css",
    "ci/cd", "git", "linux", "ai", "llm", "rag", "langchain", "prompt engineering",
    "microservices", "asyncio", "system design", "data structures"
]

ACTION_VERBS = [
    "Spearheaded", "Architected", "Engineered", "Optimized", "Scaled",
    "Deployed", "Automated", "Transformed", "Accelerated", "Pioneered"
]

class ATSSmartTailor:
    @staticmethod
    def extract_keywords(text: str) -> Set[str]:
        """Extracts unique technical and soft skill keywords from text."""
        cleaned = re.sub(r'[^a-zA-Z0-9\s/+#\.]', ' ', text.lower())
        tokens = set(cleaned.split())
        matched = set()
        
        # Match single and multi-word skills
        for skill in COMMON_TECH_SKILLS:
            if " " in skill and skill in cleaned:
                matched.add(skill)
            elif skill in tokens:
                matched.add(skill)
                
        return matched

    @staticmethod
    def calculate_ats_match(cv_text: str, job_description: str) -> Dict[str, Any]:
        """
        Calculates exact ATS compatibility score between CV and Job Description.
        """
        cv_keywords = ATSSmartTailor.extract_keywords(cv_text)
        job_keywords = ATSSmartTailor.extract_keywords(job_description)

        if not job_keywords:
            return {
                "ats_score": 85,
                "matched_keywords": list(cv_keywords),
                "missing_keywords": [],
                "match_percentage": 85.0
            }

        matched = cv_keywords.intersection(job_keywords)
        missing = job_keywords - cv_keywords
        match_ratio = len(matched) / len(job_keywords)
        ats_score = int(min(100, max(20, (match_ratio * 70) + 30)))

        return {
            "ats_score": ats_score,
            "matched_keywords": sorted(list(matched)),
            "missing_keywords": sorted(list(missing)),
            "total_job_keywords": len(job_keywords),
            "match_percentage": round(match_ratio * 100, 1)
        }

    @staticmethod
    def generate_tailored_summary(candidate_name: str, target_role: str, missing_keywords: List[str]) -> str:
        """
        Generates an ATS-optimized professional summary incorporating missing target keywords.
        """
        skills_str = ", ".join(missing_keywords[:4]) if missing_keywords else "scalable cloud backends and high-performance microservices"
        
        summary = (
            f"Results-driven {target_role} with proven track record in architecting mission-critical software. "
            f"Demonstrated mastery in {skills_str}, driving end-to-end performance optimization, "
            f"continuous deployment, and business-focused software delivery."
        )
        return summary

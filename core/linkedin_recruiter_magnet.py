"""
JobHunt Pro — LinkedIn Recruiter Algorithm Magnet (RCS Optimizer)
Transforms standard candidate profiles into search-optimized, high-visibility LinkedIn profiles
specifically calibrated for Boolean search filters used by Gulf headhunters and executive recruiters.
"""

from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class LinkedInRecruiterMagnet:
    """Optimizes LinkedIn profiles for Recruiter Search Algorithms (RCS) & Boolean Indexing."""

    def generate_optimized_headline(self, target_role: str, top_skills: List[str], target_region: str = "Riyadh & Dubai") -> str:
        """Generate high-CTR LinkedIn headline packed with search keywords and target location."""
        skills_str = " | ".join(top_skills[:3]) if top_skills else "Cloud Architecture | Distributed Systems"
        headline = f"{target_role} | {skills_str} | Scaling Tech Systems across {target_region}"
        # Max LinkedIn Headline length is 220 characters
        return headline[:220]

    def generate_recruiter_about_section(self, target_role: str, years_exp: int, skills: List[str], key_achievements: List[str]) -> str:
        """Generate structured LinkedIn 'About' summary featuring core competencies and call-to-action."""
        skills_bullets = "\n".join([f"• {s}" for s in skills[:6]])
        achievements_bullets = "\n".join([f"• {a}" for a in key_achievements[:3]]) if key_achievements else "• Led cross-functional engineering teams to scale high-throughput platforms.\n• Reduced infrastructure latency by 40% while saving cloud costs.\n• Delivered enterprise-grade solutions compliant with regional standards."

        about_text = (
            f"Passionate {target_role} with {years_exp}+ years of experience architecting and delivering high-impact systems. "
            f"Specialized in transforming business requirements into scalable, fault-tolerant solutions aligned with modern GCC standards.\n\n"
            f"🎯 Core Competencies & Tech Stack:\n{skills_bullets}\n\n"
            f"🏆 Selected Highlights:\n{achievements_bullets}\n\n"
            f"📫 Open to leadership & principal technical opportunities across Saudi Arabia (Vision 2030), UAE, and remote GCC. "
            f"Feel free to connect or reach out directly."
        )
        return about_text

    def optimize_experience_bullet_points(self, role_title: str, company: str, raw_duties: List[str]) -> List[str]:
        """Convert basic duty bullet points into high-impact, quantified achievement statements."""
        optimized = []
        action_verbs = ["Architected and scaled", "Spearheaded the design of", "Engineered high-resilience", "Streamlined cross-team"]

        for idx, duty in enumerate(raw_duties[:4]):
            verb = action_verbs[idx % len(action_verbs)]
            cleaned = duty.strip().rstrip(".")
            if not any(char.isdigit() for char in cleaned):
                # Add quantified impact metric
                optimized.append(f"{verb} {cleaned}, achieving a 35% improvement in operational throughput.")
            else:
                optimized.append(f"{verb} {cleaned}.")

        if not optimized:
            optimized = [
                "Architected and deployed distributed microservices processing 5M+ daily requests with 99.99% uptime.",
                "Spearheaded database optimization and caching strategies, reducing query latency by 65%.",
                "Mentored senior engineering teams on CI/CD pipelines and cloud security governance."
            ]
        return optimized

    def full_profile_optimization(
        self,
        candidate_name: str,
        target_role: str,
        years_experience: int = 8,
        skills: Optional[List[str]] = None,
        key_achievements: Optional[List[str]] = None,
        current_duties: Optional[List[str]] = None,
        target_city: str = "Riyadh & Dubai"
    ) -> Dict[str, Any]:
        """Produce a complete, copy-paste-ready optimized LinkedIn profile payload."""
        skills_list = skills or ["Python", "Cloud Architecture", "FastAPI", "Kubernetes", "PostgreSQL", "System Design"]
        headline = self.generate_optimized_headline(target_role, skills_list, target_city)
        about = self.generate_recruiter_about_section(target_role, years_experience, skills_list, key_achievements or [])
        experience = self.optimize_experience_bullet_points(target_role, "Current / Recent Organization", current_duties or [])

        # Estimate Recruiter Visibility Score
        score = min(98, 75 + len(skills_list) * 3)

        return {
            "candidate_name": candidate_name,
            "target_role": target_role,
            "visibility_score": score,
            "optimized_headline": headline,
            "optimized_about": about,
            "optimized_experience_bullets": experience,
            "recommended_skills_to_endorse": skills_list[:10],
            "recruiter_search_keywords": [target_role, f"Senior {target_role}", f"Lead {target_role}"] + skills_list[:5]
        }


# Global singleton instance
linkedin_recruiter_magnet = LinkedInRecruiterMagnet()

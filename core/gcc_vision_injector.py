"""
JobHunt Pro — GCC Vision 2030 & Strategic Keyword Injector Engine
Autonomous intelligence module that analyzes company location, industry, and job role
to inject high-impact national transformation alignment keywords (Saudi Vision 2030,
NEOM, UAE Centennial 2071, Dubai D33, Qatar National Vision 2030).
"""

from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Strategic GCC National Initiatives Knowledge Base
GCC_NATIONAL_STRATEGIES = {
    "saudi_arabia": {
        "country_names": ["saudi arabia", "saudi", "ksa", "riyadh", "jeddah", "khobar", "dammam", "neom"],
        "pillars": [
            "Saudi Vision 2030 National Transformation Program",
            "PIF Giga-Projects Ecosystem (NEOM, Red Sea Global, Qiddiya, ROSHN)",
            "National Industrial Development and Logistics Program (NIDLP)",
            "Financial Sector Development Program & Fintech Saudi Hub",
            "Digital Transformation & National Data and AI Authority (SDAIA) Initiatives"
        ],
        "strategic_keywords": [
            "Vision 2030 alignment", "SDAIA data governance", "local talent upskilling",
            "digital economy transformation", "PIF portfolio scalability", "Saudi cloud-first policy",
            "knowledge transfer", "high-impact Saudization optimization", "sustainable innovation"
        ],
        "recommended_tone": "Visionary, high-ownership, execution-focused with clear ROI metrics"
    },
    "united_arab_emirates": {
        "country_names": ["united arab emirates", "uae", "dubai", "abu dhabi", "sharjah", "difc", "adgm"],
        "pillars": [
            "Dubai Economic Agenda D33",
            "UAE Centennial 2071",
            "National Strategy for Artificial Intelligence 2031",
            "UAE Digital Economy Strategy & Hub71 / DIFC Innovation Ecosystem",
            "Clean Energy & Net Zero 2050 Strategic Initiative"
        ],
        "strategic_keywords": [
            "Dubai D33 economic milestone", "UAE AI 2031 integration", "agile global delivery",
            "DIFC/ADGM compliant scaling", "fintech disruption", "cloud-native resilience",
            "multicultural team leadership", "cross-border commercial impact"
        ],
        "recommended_tone": "Fast-paced, innovation-first, hyper-scalable, and internationally benchmarked"
    },
    "qatar": {
        "country_names": ["qatar", "doha", "qfc", "lusail"],
        "pillars": [
            "Qatar National Vision 2030 (QNV 2030)",
            "Third National Development Strategy (NDS3)",
            "Qatar Financial Centre (QFC) Digital Assets Lab",
            "TASMU Smart Qatar Program"
        ],
        "strategic_keywords": [
            "QNV 2030 diversification", "TASMU smart architecture", "NDS3 knowledge-based economy",
            "high-security enterprise resilience", "institutional growth enablement"
        ],
        "recommended_tone": "Institutional, prestigious, security-minded, and sustainability-aligned"
    },
    "kuwait": {
        "country_names": ["kuwait", "kuwait city", "kpc"],
        "pillars": ["New Kuwait Vision 2035 (Kuwait National Development Plan)"],
        "strategic_keywords": ["Vision 2035 digitization", "operational efficiency", "modern governance"],
        "recommended_tone": "Pragmatic, efficiency-driven, and value-oriented"
    }
}


class GCCVisionInjector:
    """Intelligent GCC Strategy & Giga-Project Contextualizer for AI SDR & CV Tailoring."""

    def detect_gcc_country(self, location_text: str, company_name: str = "", job_description: str = "") -> Optional[str]:
        """Detect which GCC country a job opportunity belongs to based on text clues."""
        combined_text = f"{location_text} {company_name} {job_description}".lower()

        for country_key, data in GCC_NATIONAL_STRATEGIES.items():
            for name_variant in data["country_names"]:
                if re.search(rf"\b{re.escape(name_variant)}\b", combined_text):
                    return country_key

        # Default fallback if GCC mentioned generically
        if any(term in combined_text for term in ["gcc", "gulf", "middle east", "mena"]):
            return "saudi_arabia"

        return None

    def calculate_alignment_score(self, cv_text: str, target_country: str) -> Dict[str, Any]:
        """Evaluate how well a candidate's CV is aligned with target GCC strategic initiatives."""
        strategy = GCC_NATIONAL_STRATEGIES.get(target_country, GCC_NATIONAL_STRATEGIES["saudi_arabia"])
        keywords = strategy["strategic_keywords"]
        cv_lower = cv_text.lower()

        matched = [kw for kw in keywords if any(word in cv_lower for word in kw.lower().split())]
        match_rate = len(matched) / len(keywords) if keywords else 0.5
        score = int(min(100, max(35, match_rate * 100 + 40)))

        return {
            "country": target_country,
            "alignment_score": score,
            "matched_themes": matched,
            "strategic_pillars": strategy["pillars"][:2],
            "key_recommendation": f"Emphasize experience in {strategy['pillars'][0]} to boost response rates."
        }

    def enrich_cover_letter(self, original_text: str, location_text: str, role_title: str, company_name: str = "") -> Dict[str, Any]:
        """Enrich a cover letter with authentic GCC vision alignment paragraphs."""
        country_key = self.detect_gcc_country(location_text, company_name)
        if not country_key:
            return {
                "is_gcc_enriched": False,
                "enriched_text": original_text,
                "alignment_metadata": None
            }

        strategy = GCC_NATIONAL_STRATEGIES[country_key]
        primary_pillar = strategy["pillars"][0]
        keyword_sample = ", ".join(strategy["strategic_keywords"][:3])

        strategic_paragraph = (
            f"\n\nFurthermore, recognizing {company_name or 'your organization'}'s pivotal role within the "
            f"{primary_pillar}, I am eager to leverage my background in {role_title} to directly support your "
            f"growth milestones, ensuring seamless execution across {keyword_sample}."
        )

        enriched_content = original_text.strip() + strategic_paragraph

        return {
            "is_gcc_enriched": True,
            "target_country": country_key,
            "primary_pillar": primary_pillar,
            "enriched_text": enriched_content,
            "tone_applied": strategy["recommended_tone"]
        }


# Global singleton instance
gcc_vision_injector = GCCVisionInjector()

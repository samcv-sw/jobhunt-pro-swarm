import re
from typing import List, Dict, Any, Tuple

class ATSResumeTailor:
    """
    Engine for analyzing candidate CVs against job descriptions,
    calculating ATS match percentage, and tailoring resume sections.
    """

    STOPWORDS = {
        "and", "the", "to", "of", "a", "an", "in", "for", "is", "on", "that", "by",
        "this", "with", "i", "you", "it", "not", "or", "be", "are", "from", "at",
        "as", "your", "all", "have", "new", "more", "an", "was", "we", "will", "home",
        "can", "us", "about", "if", "page", "my", "has", "search", "free", "but", "our",
        "one", "other", "do", "no", "information", "time", "they", "site", "he", "up",
        "may", "what", "which", "their", "news", "out", "use", "any", "there", "see",
        "only", "so", "his", "when", "contact", "here", "business", "who", "web", "also",
        "now", "help", "get", "pm", "view", "online", "first", "am", "been", "would",
        "how", "were", "me", "services", "some", "these", "click", "its", "like", "service"
    }

    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        """Extracts key technical and professional terms from text."""
        words = re.findall(r'\b[a-zA-Z0-9\+#\.]+\b', text.lower())
        keywords = [w for w in words if len(w) > 2 and w not in cls.STOPWORDS]
        return list(dict.fromkeys(keywords))  # preserve order & unique

    @classmethod
    def calculate_ats_match(cls, cv_text: str, job_description: str) -> Dict[str, Any]:
        """
        Calculates ATS match score (0-100%) between CV and Job Description.
        Returns score, matching keywords, missing keywords, and recommendations.
        """
        if not cv_text or not job_description:
            return {
                "match_score": 0.0,
                "matching_keywords": [],
                "missing_keywords": [],
                "recommendations": ["Provide both CV text and Job Description for ATS scoring."]
            }

        cv_keywords = set(cls.extract_keywords(cv_text))
        jd_keywords = set(cls.extract_keywords(job_description))

        if not jd_keywords:
            return {
                "match_score": 100.0,
                "matching_keywords": list(cv_keywords),
                "missing_keywords": [],
                "recommendations": ["Job description contains minimal keywords."]
            }

        matching = cv_keywords.intersection(jd_keywords)
        missing = jd_keywords.difference(cv_keywords)

        raw_ratio = len(matching) / len(jd_keywords)
        # Boost ratio slightly to reflect core technical alignment
        match_score = round(min(100.0, max(0.0, raw_ratio * 100 * 1.15)), 1)

        recommendations = []
        if match_score < 70.0:
            top_missing = list(missing)[:5]
            recommendations.append(f"Consider adding key terms to your CV: {', '.join(top_missing)}.")
        if "lead" in jd_keywords and "lead" not in cv_keywords:
            recommendations.append("Highlight leadership and project management accomplishments.")
        if "cisco" in jd_keywords or "python" in jd_keywords:
            recommendations.append("Ensure technical certifications and toolsets are explicitly listed.")

        if not recommendations:
            recommendations.append("Your CV is strongly aligned with this job description!")

        return {
            "match_score": match_score,
            "matching_keywords": sorted(list(matching)),
            "missing_keywords": sorted(list(missing)),
            "recommendations": recommendations
        }

    @classmethod
    def generate_tailored_summary(cls, candidate_title: str, candidate_summary: str, job_title: str, job_description: str) -> str:
        """
        Generates an optimized professional summary tailored specifically for the target job title & description.
        """
        jd_keywords = cls.extract_keywords(job_description)[:6]
        kw_str = ", ".join(jd_keywords) if jd_keywords else "IT Infrastructure & Software Systems"

        tailored = (
            f"Results-oriented {candidate_title} with proven expertise targeted for {job_title} positions. "
            f"Demonstrated track record leveraging key technical domains including {kw_str}. "
            f"{candidate_summary if candidate_summary else 'Passionate about engineering scalable systems and driving operational excellence.'}"
        )
        return tailored

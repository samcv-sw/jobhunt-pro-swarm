"""
Dual-Language ATS Heatmap & Stealth Metadata Sculptor
Advanced ATS scoring with Arabic (RTL) & English dual parsing,
interactive keyword density heatmap generator, parseability penalty checks, and XMP metadata injection.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("ats_dual_heatmap_sculptor")


class ATSDualHeatmapSculptor:
    """
    Computes bidirectional ATS keyword match density, generates heatmap representations,
    evaluates ATS parseability penalties, and prepares stealth PDF/DOCX metadata tag injections.
    """

    ARABIC_COMMON_STOPWORDS = {
        "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي", "أن", "إن", "كان", "لقد", "تم", "هو", "هي", "كل", "ما"
    }

    ENGLISH_COMMON_STOPWORDS = {
        "in", "on", "at", "to", "for", "with", "a", "an", "the", "and", "or", "is", "are", "was", "were", "been", "by", "of", "it"
    }

    ACTION_VERBS_EN = {
        "spearheaded", "orchestrated", "architected", "engineered", "accelerated", "implemented",
        "optimized", "delivered", "transformed", "scaled", "generated", "reduced", "led", "managed", "built"
    }

    ACTION_VERBS_AR = {
        "قاد", "طور", "صمم", "نفذ", "أدار", "حسن", "أطلق", "حقق", "زاد", "خفض", "بنى", "أنشأ", "أشرف"
    }

    def _is_arabic_text(self, text: str) -> bool:
        """Determines if text has predominantly Arabic characters."""
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        return arabic_chars > 20 or (len(text) > 0 and (arabic_chars / max(1, len(text.split()))) > 0.3)

    def _extract_tokens(self, text: str, is_arabic: bool = False) -> List[str]:
        """Tokenizes and cleans text removing stopwords."""
        words = re.findall(r"[\w\u0600-\u06FF]+", text.lower())
        stopwords = self.ARABIC_COMMON_STOPWORDS if is_arabic else self.ENGLISH_COMMON_STOPWORDS
        return [w for w in words if w not in stopwords and len(w) > 2]

    def _evaluate_parseability_penalties(self, cv_text: str, is_arabic: bool = False) -> Dict[str, Any]:
        """
        Detects common ATS parsing blockers such as missing contact sections,
        lack of quantifiable metrics, or complex structures.
        """
        penalties = []
        score_deduction = 0.0

        # Check for numbers / quantifiable metrics (e.g. 20%, $50k, 100+)
        has_metrics = bool(re.search(r"(\d+[\%kK\$\+xX]|\d+\s*(ألف|مليون|بالمئة|٪))", cv_text))
        if not has_metrics:
            penalties.append({
                "issue": "غياب الأرقام والنتائج القابلة للقياس (Lack of Quantifiable Metrics)" if is_arabic else "Lack of Quantifiable Metrics (e.g. percentages, numbers, scale)",
                "impact": -5.0,
                "suggestion": "أضف أرقاماً تدل على إنجازاتك (مثل: زيادة المبيعات بنسبة 25%)" if is_arabic else "Add measurable metrics (e.g., increased revenue by 25%)"
            })
            score_deduction += 5.0

        # Check for Contact Info
        has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cv_text))
        if not has_email:
            penalties.append({
                "issue": "عدم وجود بريد إلكتروني واضح (Missing Visible Email)" if is_arabic else "Missing Visible Email Header",
                "impact": -10.0,
                "suggestion": "ضع البريد الإلكتروني في أعلى الصفحة لسهولة القراءة" if is_arabic else "Ensure email address is present in standard text format at top"
            })
            score_deduction += 10.0

        # Check for Action Verbs
        tokens_set = set(re.findall(r"[\w\u0600-\u06FF]+", cv_text.lower()))
        action_verb_pool = self.ACTION_VERBS_AR if is_arabic else self.ACTION_VERBS_EN
        action_verb_count = len(tokens_set.intersection(action_verb_pool))
        if action_verb_count < 3:
            penalties.append({
                "issue": "قلة الأفعال القوية والإنجازات (Low Action Verb Density)" if is_arabic else "Low Action Verb Density",
                "impact": -5.0,
                "suggestion": "استخدم أفعال قيادية قوية في بداية كل نقطة" if is_arabic else "Begin bullet points with strong power action verbs (e.g. Architected, Optimized)"
            })
            score_deduction += 5.0

        return {
            "deductions_total": score_deduction,
            "penalties_count": len(penalties),
            "penalties": penalties,
            "action_verb_count": action_verb_count,
            "has_metrics": has_metrics,
            "has_email": has_email
        }

    def analyze_dual_ats(self, cv_text: str, jd_text: str, is_arabic: Optional[bool] = None) -> Dict[str, Any]:
        """
        Calculates ATS matching score, classifies keyword distribution, and applies parseability checks.
        """
        if is_arabic is None:
            is_arabic = self._is_arabic_text(cv_text) or self._is_arabic_text(jd_text)

        cv_tokens = self._extract_tokens(cv_text, is_arabic=is_arabic)
        jd_tokens = self._extract_tokens(jd_text, is_arabic=is_arabic)

        jd_unique: Set[str] = set(jd_tokens)
        cv_freq: Dict[str, int] = {}
        for token in cv_tokens:
            cv_freq[token] = cv_freq.get(token, 0) + 1

        matched_keywords = []
        missing_keywords = []
        heatmap_nodes = []

        for kw in jd_unique:
            count = cv_freq.get(kw, 0)
            if count == 0:
                missing_keywords.append(kw)
                status = "missing"
            elif count == 1:
                status = "moderate"
                matched_keywords.append(kw)
            elif 2 <= count <= 5:
                status = "optimal"
                matched_keywords.append(kw)
            else:
                status = "stuffed"
                matched_keywords.append(kw)

            heatmap_nodes.append({
                "keyword": kw,
                "frequency_in_cv": count,
                "status": status,
                "density_weight": min(1.0, count / 4.0)
            })

        total_jd = len(jd_unique) if jd_unique else 1
        raw_score = (len(matched_keywords) / total_jd) * 100.0

        parseability = self._evaluate_parseability_penalties(cv_text, is_arabic=is_arabic)
        deduction = min(10.0, parseability["deductions_total"] * 0.4)
        final_score = max(45.0, min(100.0, raw_score + (12.0 if is_arabic else 8.0) - deduction)) if matched_keywords else 10.0

        # Sort heatmap by density weight descending
        heatmap_nodes.sort(key=lambda x: x["frequency_in_cv"], reverse=True)

        return {
            "ats_score": round(final_score, 1),
            "raw_match_percentage": round(raw_score, 1),
            "language": "arabic" if is_arabic else "english",
            "direction": "rtl" if is_arabic else "ltr",
            "font_family": "Cairo, Tajawal, IBM Plex Arabic, sans-serif" if is_arabic else "Inter, system-ui, sans-serif",
            "total_job_keywords": len(jd_unique),
            "matched_keywords_count": len(matched_keywords),
            "missing_keywords_count": len(missing_keywords),
            "missing_keywords": missing_keywords[:20],
            "matched_keywords": matched_keywords[:20],
            "heatmap": heatmap_nodes[:35],
            "parseability_audit": parseability
        }

    def generate_stealth_xmp_metadata(self, candidate_name: str, target_role: str, keywords: List[str]) -> Dict[str, Any]:
        """
        Generates XML XMP metadata tags to inject into PDF/DOCX for ATS search indexers.
        """
        kw_string = ", ".join(keywords[:25])
        xmp_xml = f"""<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:pdf="http://ns.adobe.com/pdf/1.3/">
   <dc:title>{candidate_name} - {target_role} CV</dc:title>
   <dc:creator>{candidate_name}</dc:creator>
   <dc:description>Executive Resume tailored for {target_role} role</dc:description>
   <dc:subject>
    <rdf:Bag>
     {"".join(f"<rdf:li>{kw}</rdf:li>" for kw in keywords[:20])}
    </rdf:Bag>
   </dc:subject>
   <pdf:Keywords>{kw_string}</pdf:Keywords>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

        return {
            "candidate_name": candidate_name,
            "target_role": target_role,
            "injected_keywords_count": len(keywords[:25]),
            "xmp_packet": xmp_xml.strip(),
            "raw_xmp_packet": xmp_xml.strip()
        }


# Global singleton
ats_dual_sculptor = ATSDualHeatmapSculptor()
ats_dual_heatmap_sculptor = ats_dual_sculptor

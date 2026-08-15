"""
GCC Labor Law & Employment Contract Analyzer
JobHunt Pro SaaS - Audits job offer letters and contracts against Saudi Qiwa & UAE MOHRE labor standards.
"""
from typing import Dict, List, Any, Optional


class GccContractAnalyzer:
    """
    Parses contract text and flags non-compliant clauses, excessive non-compete terms,
    and hidden probation penalties under Saudi & UAE labor laws.
    """

    @classmethod
    def analyze_contract(
        cls,
        contract_text: str,
        jurisdiction: str = "saudi_arabia",
        basic_salary: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Scans contract text for critical clauses and generates compliance scorecard.
        """
        text_lower = contract_text.lower()
        findings = []
        risk_score = 15  # Baseline low risk

        # 1. Check Probation Period
        if "probation" in text_lower or "تجربة" in text_lower or "فترة التجربة" in text_lower:
            if "180" in text_lower or "6 months" in text_lower or "ستة أشهر" in text_lower:
                findings.append({
                    "clause": "Probation Period (فترة التجربة)",
                    "status": "CAUTION",
                    "detail": "Probation is set to 180 days. Under Saudi Labor Law Article 53, standard probation is 90 days; extending to 180 days requires explicit mutual written consent after work commencement."
                })
                risk_score += 15
            else:
                findings.append({
                    "clause": "Probation Period",
                    "status": "COMPLIANT",
                    "detail": "Probation terms align with standard 90-day statutory limits."
                })
        else:
            findings.append({
                "clause": "Probation Period",
                "status": "INFO",
                "detail": "No explicit probation clause detected."
            })

        # 2. Check Non-Compete Clause
        if "non-compete" in text_lower or "عدم منافسة" in text_lower or "عدم المنافسة" in text_lower:
            if "3 years" in text_lower or "5 years" in text_lower or "ثلاث سنوات" in text_lower:
                findings.append({
                    "clause": "Non-Compete Clause (شرط عدم المنافسة)",
                    "status": "NON_COMPLIANT_WARNING",
                    "detail": "Non-compete exceeds 2 years. Under Article 83 of Saudi Labor Law, non-compete restrictions cannot legally exceed 2 years and must be strictly bounded by geographical scope."
                })
                risk_score += 25
            else:
                findings.append({
                    "clause": "Non-Compete Clause",
                    "status": "COMPLIANT",
                    "detail": "Non-compete clause is reasonable and bounded by statutory timeframes."
                })

        # 3. Check End of Service Benefits (EOSB)
        if "end of service" in text_lower or "مكافأة نهاية الخدمة" in text_lower or "gratuity" in text_lower:
            findings.append({
                "clause": "End of Service Indemnity (مكافأة نهاية الخدمة)",
                "status": "COMPLIANT",
                "detail": "Explicitly referenced. Guaranteed under Article 84 of Saudi Labor Law / UAE Decree 33."
            })
        else:
            findings.append({
                "clause": "End of Service Indemnity",
                "status": "RECOMMENDATION",
                "detail": "Ensure contract references statutory statutory EOSB rights."
            })

        # Final Verdict
        if risk_score <= 25:
            verdict_ar = "العقد متوافق وممتاز ومحمي قانونياً بنسبة عالية."
            verdict_en = "Contract is highly compliant with GCC labor regulations."
            safety_rating = "Grade A (Safe to Sign)"
        elif risk_score <= 50:
            verdict_ar = "العقد جيد بشكل عام مع وجود بعض البنود التي يُفضل توضيحها كتابياً."
            verdict_en = "Contract is generally sound with minor clauses needing clarification."
            safety_rating = "Grade B (Minor Review Recommended)"
        else:
            verdict_ar = "يحتوي العقد على شروط مشددة (مثل عدم المنافسة أو فترة التجربة) تتطلب تعديلاً قبل التوقيع."
            verdict_en = "Contract contains aggressive restrictive covenants requiring negotiation."
            safety_rating = "Grade C (Negotiation Required)"

        return {
            "jurisdiction": jurisdiction.upper(),
            "overall_safety_rating": safety_rating,
            "risk_score_percentage": min(100, risk_score),
            "verdict_ar": verdict_ar,
            "verdict_en": verdict_en,
            "clauses_analyzed": findings,
            "negotiation_power_tips_ar": [
                "اطلب تحديد النطاق الجغرافي لشرط عدم المنافسة في مدينة عملك فقط.",
                "تأكد من فصل الراتب الأساسي عن بدلات السكن والمواصلات بوضوح لأن مكافأة نهاية الخدمة تُحسب على الأساسي فقط."
            ]
        }


# Global singleton instance
gcc_contract_analyzer = GccContractAnalyzer()

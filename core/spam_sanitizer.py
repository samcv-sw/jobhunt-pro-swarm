"""
JobHunt Pro SaaS — Real-Time Bilingual Spam Trigger Word Sanitizer & Score Engine.
Scans cold email subject lines and body text in English and Arabic for spam triggers,
calculates an objective Deliverability Risk Score (0-100), and replaces risky terms
with high-converting, professional alternatives.
"""

from typing import Dict, List, Any, Tuple
import re

# High-risk trigger word dictionaries and safe psychographic replacements
ENGLISH_SPAM_REPLACEMENTS: Dict[str, str] = {
    r"\b100%\s*free\b": "complimentary",
    r"\bfree\b": "included",
    r"\bguaranteed\b": "proven",
    r"\bmake\s*money\b": "drive revenue",
    r"\bno\s*risk\b": "reliable",
    r"\bact\s*now\b": "at your earliest convenience",
    r"\burgent\b": "time-sensitive",
    r"\blimited\s*time\b": "current",
    r"\bwinner\b": "selected",
    r"\bcongratulations\b": "pleased to connect",
    r"\bclick\s*here\b": "view details here",
    r"\bbuy\s*now\b": "get started",
    r"\bcheap\b": "cost-effective",
    r"\blowest\s*price\b": "competitive rate",
    r"\beasy\s*money\b": "efficient growth",
    r"\bmillion\s*dollars\b": "substantial scale",
    r"\bno\s*credit\s*card\s*required\b": "direct access",
    r"\binstant\s*access\b": "immediate availability",
}

ARABIC_SPAM_REPLACEMENTS: Dict[str, str] = {
    r"مجاني\s*100%": "متاح للمعاينة",
    r"مجاناً": "متاح مباشرة",
    r"مجاني": "متاح",
    r"اربح\s*الآن": "عزز نتائجك",
    r"ربح\s*سريع": "نمو مستدام",
    r"مضمون\s*100%": "موثوق ومجرب",
    r"مضمون": "موثوق",
    r"فرصة\s*لن\s*تتكرر": "فرصة نوعية",
    r"عاجل\s*جداً": "مهم لجدولكم",
    r"عاجل": "في الوقت المناسب",
    r"اضغط\s*هنا": "للاطلاع على التفاصيل",
    r"اشتري\s*الآن": "ابدأ الآن",
    r"بدون\s*أي\s*تكلفة": "بأعلى كفاءة",
    r"أرخص\s*سعر": "بقيمة تنافسية",
    r"مبروك": "يسعدنا التواصل معكم",
    r"سارع\s*قبل\s*الانتهاء": "يسرنا التنسيق معكم",
}


class SpamSanitizer:
    """
    Bilingual Spam Sanitizer & Deliverability Risk Evaluator.
    Evaluates cold email content and sanitizes spam triggers to maximize Inbox landing rates.
    """

    def __init__(self):
        self.en_replacements = ENGLISH_SPAM_REPLACEMENTS
        self.ar_replacements = ARABIC_SPAM_REPLACEMENTS

    def calculate_spam_score(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Calculates spam score from 0 (Perfect/Clean) to 100 (High Risk Spam).
        """
        score = 0
        detected_triggers: List[str] = []
        recommendations: List[str] = []

        combined_text = f"{subject} {body}"

        # 1. Check English triggers
        for pattern in self.en_replacements.keys():
            matches = re.findall(pattern, combined_text, flags=re.IGNORECASE)
            if matches:
                detected_triggers.extend([m.lower() for m in matches])
                score += len(matches) * 12

        # 2. Check Arabic triggers
        for pattern in self.ar_replacements.keys():
            matches = re.findall(pattern, combined_text)
            if matches:
                detected_triggers.extend(matches)
                score += len(matches) * 12

        # 3. Check for excessive exclamation marks or all-caps in English
        exclamations = combined_text.count("!") + combined_text.count("؟")
        if exclamations > 2:
            score += min(exclamations * 5, 20)
            recommendations.append("Reduce exclamation marks to avoid promotional filters.")

        # Check ALL CAPS in English words (3+ consecutive all caps words)
        all_caps_words = re.findall(r"\b[A-Z]{3,}\b", subject)
        if all_caps_words:
            score += len(all_caps_words) * 8
            recommendations.append("Avoid ALL-CAPS words in subject line.")

        # 4. Check excessive links
        links = re.findall(r"https?://\S+|www\.\S+", body)
        if len(links) > 2:
            score += (len(links) - 2) * 10
            recommendations.append("Limit email body to maximum 1-2 relevant links.")

        # Cap score between 0 and 100
        final_score = min(score, 100)

        # Determine risk classification
        if final_score < 20:
            classification = "CLEAN_EXCELLENT"
            inbox_probability = "99%+"
        elif final_score < 45:
            classification = "MODERATE_ACCEPTABLE"
            inbox_probability = "85-95%"
        elif final_score < 70:
            classification = "HIGH_RISK"
            inbox_probability = "50-70%"
        else:
            classification = "CRITICAL_SPAM_TRAP"
            inbox_probability = "<40%"

        return {
            "spam_score": final_score,
            "classification": classification,
            "inbox_probability": inbox_probability,
            "detected_triggers": list(set(detected_triggers)),
            "trigger_count": len(detected_triggers),
            "recommendations": recommendations,
            "is_safe_to_send": final_score < 50,
        }

    def sanitize_content(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Automatically replaces detected spam keywords with psychologically safe alternatives.
        """
        sanitized_subject = subject
        sanitized_body = body
        applied_replacements: List[Tuple[str, str]] = []

        # Replace English triggers
        for pattern, replacement in self.en_replacements.items():
            if re.search(pattern, sanitized_subject, flags=re.IGNORECASE):
                sanitized_subject = re.sub(pattern, replacement, sanitized_subject, flags=re.IGNORECASE)
                applied_replacements.append((pattern, replacement))
            if re.search(pattern, sanitized_body, flags=re.IGNORECASE):
                sanitized_body = re.sub(pattern, replacement, sanitized_body, flags=re.IGNORECASE)
                applied_replacements.append((pattern, replacement))

        # Replace Arabic triggers
        for pattern, replacement in self.ar_replacements.items():
            if re.search(pattern, sanitized_subject):
                sanitized_subject = re.sub(pattern, replacement, sanitized_subject)
                applied_replacements.append((pattern, replacement))
            if re.search(pattern, sanitized_body):
                sanitized_body = re.sub(pattern, replacement, sanitized_body)
                applied_replacements.append((pattern, replacement))

        # Clean excessive punctuation
        sanitized_subject = re.sub(r"[!！]{2,}", "!", sanitized_subject)
        sanitized_body = re.sub(r"[!！]{2,}", "!", sanitized_body)

        post_audit = self.calculate_spam_score(sanitized_subject, sanitized_body)

        return {
            "original_subject": subject,
            "sanitized_subject": sanitized_subject,
            "original_body": body,
            "sanitized_body": sanitized_body,
            "replacements_applied_count": len(applied_replacements),
            "post_audit": post_audit,
        }


# Singleton instance for high-speed module reuse
spam_sanitizer = SpamSanitizer()

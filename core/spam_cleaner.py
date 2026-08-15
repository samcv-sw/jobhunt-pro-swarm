import re
from typing import Dict, Any, List

# Bilingual Spam Triggers & Recruiter-Friendly Alternatives
SPAM_TRIGGER_SYNONYMS = {
    # English Triggers
    r"\b100%\s+free\b": "completely complimentary",
    r"\bmake\s+money\b": "generate revenue",
    r"\bguaranteed\s+response\b": "committed reply",
    r"\bwinner\b": "successful candidate",
    r"\bwork\s+from\s+home\b": "remote location",
    r"\bno\s+investment\b": "zero upfront cost",
    r"\bunlimited\b": "substantial",
    r"\bapply\s+now\b": "submit your application",
    r"\burgent\b": "prioritized",
    r"\bimmediate\b": "prioritized",
    r"\bbest\s+price\b": "optimal value",
    r"\bsave\s+cash\b": "reduce expenditure",
    r"\bact\s+now\b": "take action today",
    r"\brisk\s+free\b": "secured",
    r"\bextra\s+income\b": "supplemental revenue",
    r"\bclick\s+here\b": "review details at the link",
    r"\bcongratulations\b": "pleased to connect",
    r"\bno\s+catch\b": "transparent terms",
    r"\bcash\s+bonus\b": "incentive package",
    r"\bexclusive\s+deal\b": "tailored opportunity",
    # Arabic Triggers
    r"مجاني\s+بالكامل": "مقدّم كخدمة مخصصة",
    r"مجاناً": "بدون تكلفة إضافية",
    r"فرصة\s+ذهبية": "فرصة نوعية متميزة",
    r"ربح\s+سريع": "عائد استثماري مستدام",
    r"مضمون\s+100%": "موثوق وذو أولوية عالية",
    r"عاجل": "ذو أولوية",
    r"اضغط\s+هنا": "يمكنكم الاطلاع عبر الرابط",
    r"بدون\s+مقدم": "بشروط مرنة",
    r"وظيفة\s+أحلامك": "مسار وظيفي واعد",
    r"دخل\s+إضافي": "عوائد مهنية متقدمة",
    r"سارع\s+الآن": "يُرجى التكرم بالاطلاع"
}


def sanitize_spam_triggers(text: str) -> str:
    """Scans and replaces common email spam trigger words with recruiter-friendly
    synonyms to improve email deliverability and avoid landing in the spam folder.
    """
    if not text:
        return ""

    cleaned = text
    for pattern, replacement in SPAM_TRIGGER_SYNONYMS.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned


def analyze_content_deliverability(text: str) -> Dict[str, Any]:
    """Analyzes email/outreach copy for spam trigger words across English and Arabic,
    calculating deliverability health score (0-100%) and actionable fixes.
    """
    if not text or not text.strip():
        return {
            "health_score": 100,
            "risk_level": "EXCELLENT",
            "detected_triggers": [],
            "sanitized_text": "",
            "word_count": 0,
            "spam_density_percent": 0.0,
            "recommendations": ["Content is clean and ready for dispatch."]
        }

    words = text.split()
    total_words = max(1, len(words))
    detected: List[Dict[str, str]] = []

    for pattern, replacement in SPAM_TRIGGER_SYNONYMS.items():
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if matches:
            for match in matches:
                detected.append({
                    "matched_text": match.group(0),
                    "suggested_alternative": replacement,
                    "severity": "HIGH" if any(w in match.group(0).lower() for w in ["free", "مجانا", "100%", "cash", "ربح"]) else "MEDIUM"
                })

    # Calculate deliverability score deduction (10 points per high, 5 per medium)
    penalty = sum(10 if d["severity"] == "HIGH" else 5 for d in detected)
    health_score = max(0, min(100, 100 - penalty))

    risk_level = "EXCELLENT"
    if health_score < 70:
        risk_level = "HIGH_RISK"
    elif health_score < 90:
        risk_level = "MODERATE"

    sanitized = sanitize_spam_triggers(text)
    spam_density = round((len(detected) / total_words) * 100, 2)

    recommendations = []
    if detected:
        recommendations.append(f"Found {len(detected)} potential spam trigger(s). Consider replacing them with professional alternatives.")
    else:
        recommendations.append("Copy contains zero known spam triggers. High inbox placement likelihood.")

    return {
        "health_score": health_score,
        "risk_level": risk_level,
        "detected_triggers": detected,
        "sanitized_text": sanitized,
        "word_count": total_words,
        "spam_density_percent": spam_density,
        "recommendations": recommendations
    }


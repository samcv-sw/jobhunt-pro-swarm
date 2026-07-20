import re

SPAM_TRIGGER_SYNONYMS = {
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
}


def sanitize_spam_triggers(text: str) -> str:
    """Scans and replaces common email spam trigger words with recruiter-friendly
    synonyms to improve email deliverability and avoid landing in the spam folder.
    """
    if not text:
        return ""

    cleaned = text
    for pattern, replacement in SPAM_TRIGGER_SYNONYMS.items():
        # Perform case-insensitive substitution keeping the case if possible
        # Simple implementation using re.sub with case-insensitive flag
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned

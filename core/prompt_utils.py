import re

BOILERPLATE_PATTERNS = [
    # Equal Opportunity Employer statements
    r"(?i)\bwe\s+are\s+an\s+equal\s+opportunity\s+employer\b.*?(?=\n\n|\Z)",
    r"(?i)\bapplicants\s+will\s+receive\s+consideration\s+for\s+employment\b.*?(?=\n\n|\Z)",
    r"(?i)\bwe\s+do\s+not\s+discriminate\b.*?(?=\n\n|\Z)",
    r"(?i)\bcommitted\s+to\s+creating\s+a\s+diverse\s+environment\b.*?(?=\n\n|\Z)",
    # COVID statements
    r"(?i)\bcovid-19\s+vaccination\b.*?(?=\n\n|\Z)",
    # Generic benefits list boilerplate
    r"(?i)\bwe\s+offer\s+a\s+competitive\s+benefits\s+package\b.*?(?=\n\n|\Z)",
    r"(?i)\bmedical,\s+dental,\s+vision,\s+401\(k\)\b.*?(?=\n\n|\Z)",
]


def minify_prompt(prompt_text: str) -> str:
    """Minifies prompt text by stripping leading/trailing spaces, collapsing multiple spaces,
    and collapsing multiple newlines into single newlines.
    """
    if not prompt_text:
        return ""

    lines = []
    for line in prompt_text.splitlines():
        # Strip leading and trailing spaces
        cleaned = line.strip()
        # Collapse multiple spaces to a single space
        cleaned = re.sub(r" {2,}", " ", cleaned)
        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)


def prune_job_description(description: str) -> str:
    """Removes boilerplate/legal text (e.g. EEOC statements, generic benefits, COVID mandates)
    from job descriptions to reduce token footprint while keeping core requirements.
    """
    if not description:
        return ""

    cleaned = description
    for pattern in BOILERPLATE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned)

    # Remove excessive blank lines resulting from cleaning
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


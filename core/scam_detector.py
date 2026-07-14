"""
ScamDetector v1 — JobHunt Pro Scam & Fraud Protection
Prevents sending applications to MLM schemes, crypto scams, fake job postings, etc.

Created: 2026-06-24 — Deep Scan Session
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# SCAM PATTERNS
# ══════════════════════════════════════════════════════════════════════════

SCAM_COMPANY_PATTERNS = {
    "mlm_pyramid": [
        "amway",
        "herbalife",
        "nu skin",
        "primerica",
        "doterra",
        "young living",
        "world ventures",
        "isagenix",
        "usana",
        "arbonne",
        "monat",
        "senegence",
        "mary kay",
        "avon cosmetics",
        "avon products",
        "avon representative",
        "pampered chef",
        "tupperware",
        "scentsy",
        "kyani",
        "jeunesse",
        "qnet",
        "organo gold",
        "forever living",
        "it works global",
        "lifevantage",
        "melaleuca",
        "younique",
        "paparazzi accessories",
        "color street",
        "thirty-one gifts",
        "norwex",
        "partylite",
        "lularoe",
        "seacret",
        "jem jewels",
    ],
    "crypto_fraud": [
        "bitconnect",
        "onecoin",
        "plus token",
        "wootrade",
        "celsius network",
        "blockfi",
        "genesis crypto",
        "genesis trading",
        "genesis global capital",
        "genesis block",
        "gemini earn",
        "crypto exchange",
        "trading signals",
        "defi yield",
        "binary options",
        "forex signals",
        "trading bot",
        "crypto trading",
        "crypto arbitrage",
        "nft flipping",
        "bitcoin mining",
        "cloud mining",
        "coinbase remote",
        "binance remote",
        "kraken support",
        "crypto wallet support",
    ],
    "fake_agency": [
        "top recruitment",
        "expert staffing",
        "pro hiring",
        "elite placements",
        "alpha recruit",
        "prime talent",
        "global placement",
        "direct staffing solutions",
        "recruitment agency hiring 100 junior it",
        "hiring 50+ positions",
        "urgent requirement 500+",
        "mass recruitment",
        "walk in interview 200+",
    ],
    "ponzi_schemes": [
        "profit sharing",
        "passive income",
        "residual income",
        "financial freedom",
        "retire early",
        "earn while you sleep",
        "make money online",
        "work from home earn",
        "get rich quick",
        "double your income",
        "unlimited earning potential",
        "$500/day",
        "$1000/week",
    ],
    "data_harvesting": [
        "data entry $",
        "typing jobs $",
        "form filling",
        "online survey",
        "mystery shopper",
        "envelope stuffing",
        "package forwarding",
        "reshipping",
        "rebate processing",
        "payment processing agent",
        "money transfer agent",
        "send/receive packages",
        "work at home assembly",
    ],
    "ghost_jobs": [
        "urgent hiring",
        "immediate joining",
        "no interview",
        "direct payroll",
        "apply by replying",
        "apply by whatsapp",
        "interview via telegram",
        "whatsapp interview only",
        "telegram interview",
        "no experience required $",
        "work from home no experience",
    ],
    # ── 2025 Emerging Scam Categories ──────────────────────────────────
    "ai_phishing_jobs": [
        "chatgpt evaluator remote $",
        "ai trainer work from home",
        "llm tester no experience",
        "ai data labeler $500",
        "prompt evaluator $1000",
        "ai model tester part time",
        "openai contractor remote $300",
        "google deepmind remote tester",
        "anthropic evaluator work",
    ],
    "discord_signal_scams": [
        "interview via discord",
        "apply on discord",
        "discord interview link",
        "signal interview",
        "apply via signal",
        "contact on discord",
        "job offer discord",
        "job discord server",
    ],
    "social_engineering": [
        "send your bank details",
        "bank account for payroll",
        "advance fee",
        "training fee required",
        "pay for kit",
        "equipment deposit",
        "background check fee",
        "visa processing fee",
        "pay before starting",
        "upfront investment",
        "wire transfer advance",
        "western union payment",
        "gift card payment",
        "zelle payment first",
    ],
}

SCAM_TITLE_KEYWORDS = [
    "$500/day",
    "$1000/week",
    "make money",
    "get rich",
    "work from home $",
    "passive income",
    "no experience $",
    "immediate start $",
    "guaranteed income",
    "unlimited earning",
    "financial freedom",
    "data entry clerk",
    "form filler",
    "online typist",
    "mystery shopper",
    "package handler home",
]

SCAM_TLD_BLOCKLIST = [
    ".xyz",
    ".top",
    ".tk",
    ".ml",
    ".ga",
    ".cf",
    ".gq",
    ".work",
    ".click",
    ".link",
    ".country",
    ".loan",
    ".stream",
    ".download",
    ".racing",
    # 2025 additions
    ".vip",
    ".icu",
    ".buzz",
    ".fun",
    ".monster",
    ".cyou",
    ".sbs",
    ".quest",
]

SCAM_SALARY_FLAGS = [
    # "Too good to be true" salary for entry/network roles
    (5000, "monthly"),  # $5K+/month for entry-level = suspect
    (200, "hourly"),  # $200+/hour for general roles
]

import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))
try:
    import config

    SITE_URL = getattr(config, "SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip(
        "/"
    )
    PHYSICAL_ADDRESS = getattr(config, "CANDIDATE_ADDRESS", "Beirut, Lebanon")
except Exception:
    import os

    SITE_URL = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip("/")
    PHYSICAL_ADDRESS = "Beirut, Lebanon"
UNSUBSCRIBE_URL = f"{SITE_URL}/unsubscribe"


class ScamDetector:
    """Detects scam/fraudulent job postings before they reach candidates."""

    def __init__(self):
        self._compiled_company_regex = {}
        for category, patterns in SCAM_COMPANY_PATTERNS.items():
            regex_parts = []
            for p in patterns:
                escaped = re.escape(p)
                # Intelligently add word boundary if pattern starts/ends with alphanumeric
                start_boundary = r"\b" if p[0].isalnum() or p[0] == "_" else ""
                end_boundary = r"\b" if p[-1].isalnum() or p[-1] == "_" else ""
                regex_parts.append(f"{start_boundary}{escaped}{end_boundary}")
            # Combine all patterns for a category into a single regex union
            self._compiled_company_regex[category] = re.compile(
                "|".join(regex_parts), re.IGNORECASE
            )

        # Combine all title keywords into a single regex union using smart word boundaries
        title_parts = []
        for k in SCAM_TITLE_KEYWORDS:
            escaped = re.escape(k)
            start_boundary = r"\b" if k[0].isalnum() or k[0] == "_" else ""
            end_boundary = r"\b" if k[-1].isalnum() or k[-1] == "_" else ""
            title_parts.append(f"{start_boundary}{escaped}{end_boundary}")
        self._compiled_titles_regex = re.compile("|".join(title_parts), re.IGNORECASE)

        self._tld_re = re.compile(
            r"\.(xyz|top|tk|ml|ga|cf|gq|work|click|link|country|loan|stream|download|racing)$",
            re.IGNORECASE,
        )

    def is_scam(self, job: dict[str, Any]) -> tuple[bool, str]:
        """
        Check if a job posting is a scam.
        Returns (is_scam: bool, reason: str)
        """
        is_detected, reason = self._check_is_scam(job)
        if is_detected:
            company = (job.get("company") or "").strip()
            title = (job.get("title") or "").strip()
            logger.warning(
                f"[ScamDetector] Scam flagged: {reason} (Company: '{company}', Title: '{title}')"
            )
        return is_detected, reason

    def _check_tlds_and_emails(self, url: str, email: str) -> tuple[bool, str]:
        """
        Check job URL and contact email for suspicious top-level domains (TLDs).

        Args:
            url: The application or job URL.
            email: The contact email address.

        Returns:
            A tuple of (is_suspicious, reason).
        """
        if url:
            from urllib.parse import urlparse

            try:
                domain = urlparse(url).netloc.lower()
                if self._tld_re.search(domain):
                    return True, f"Suspicious TLD detected: {domain}"
            except Exception:
                pass

        if email:
            try:
                email_domain = email.split("@")[-1].lower()
                if self._tld_re.search(email_domain):
                    return True, f"Suspicious email TLD: {email_domain}"
            except Exception:
                pass

        return False, ""

    def _check_salary_sanity(self, salary: Any, combined: str) -> tuple[bool, str]:
        """
        Check if the listed salary is realistic for the job scope.

        Args:
            salary: The salary value (numeric or string representation).
            combined: Combined job details text for context keyword lookup.

        Returns:
            A tuple of (is_suspicious, reason).
        """
        if not salary:
            return False, ""

        try:
            s = float(salary)
            # Differentiate periods based on magnitude
            if s > 30000:
                monthly_equiv = s / 12
                period = "yearly"
            elif s > 1000:
                monthly_equiv = s
                period = "monthly"
            else:
                monthly_equiv = s * 160  # assume 160 hours/month
                period = "hourly"

            # For a Senior Network Engineer, high salaries are normal.
            # Only block if salary is completely absurd (> $40K/month)
            # OR if it's high (> $10K/month) and combined with low-skill keywords.
            is_suspicious = False
            if monthly_equiv > 40000:
                is_suspicious = True
            elif monthly_equiv > 10000:
                low_skill_kws = [
                    "data entry",
                    "typing",
                    "assistant",
                    "clerk",
                    "form filler",
                    "survey",
                ]
                if any(k in combined for k in low_skill_kws):
                    is_suspicious = True

            if is_suspicious:
                return (
                    True,
                    f"Suspicious salary: ${s:,.0f}/{period} (too high for job scope)",
                )
        except (ValueError, TypeError):
            pass

        return False, ""

    def _check_chat_platforms_and_flags(self, combined_lower: str) -> tuple[bool, str]:
        """
        Check for chat-platform recruitment patterns, fraud indicators, and entry/urgency count.

        Args:
            combined_lower: Lowercased combined job details.

        Returns:
            A tuple of (is_scam, reason).
        """
        if "telegram" in combined_lower and any(
            w in combined_lower
            for w in ["interview", "recruit", "hiring", "apply", "contact"]
        ):
            return True, "Scam detected: Telegram recruitment/interview channel"
        if "whatsapp" in combined_lower and any(
            w in combined_lower
            for w in [
                "interview",
                "recruit",
                "hiring",
                "apply",
                "contact",
                "cv",
                "send",
            ]
        ):
            return True, "Scam detected: WhatsApp recruitment/interview channel"
        if "discord" in combined_lower and any(
            w in combined_lower
            for w in ["interview", "recruit", "hiring", "apply", "job"]
        ):
            return True, "Scam detected: Discord recruitment channel (2025 scam vector)"
        if "signal" in combined_lower and any(
            w in combined_lower for w in ["interview", "apply", "job offer", "hiring"]
        ):
            return (
                True,
                "Scam detected: Signal messaging recruitment (2025 scam vector)",
            )

        high_risk_scam_flags = [
            "envelope stuffing",
            "package forwarding",
            "package handler home",
            "send your bank details",
            "advance fee",
            "training fee required",
            "pay for kit",
            "equipment deposit",
            "background check fee",
            "visa processing fee",
            "pay before starting",
            "upfront investment",
            "wire transfer advance",
            "western union payment",
            "gift card payment",
            "zelle payment first",
        ]
        if any(f in combined_lower for f in high_risk_scam_flags):
            return True, "Scam detected: package or work-from-home fraud flag"

        # Mild urgency/entry indicators (only block if multiple are present AND combined with low-skill terms)
        mild_flags = [
            "no interview",
            "no experience",
            "immediate hire",
            "walk in",
            "urgent opening",
        ]
        mild_count = sum(1 for f in mild_flags if f in combined_lower)
        if mild_count >= 3:
            low_skill_kws = [
                "data entry",
                "typing",
                "assistant",
                "clerk",
                "form filler",
                "survey",
                "simple task",
            ]
            if any(k in combined_lower for k in low_skill_kws):
                return (
                    True,
                    "Ghost/too-good-to-be-true job (multiple urgency/low-skill flags)",
                )

        return False, ""

    def _check_is_scam(self, job: dict[str, Any]) -> tuple[bool, str]:
        company = (job.get("company") or "").strip()
        title = (job.get("title") or "").strip()
        snippet = (job.get("snippet") or job.get("description") or "").strip()
        url = (job.get("url") or job.get("apply_url") or "").strip()
        email = (job.get("email") or "").strip()
        salary = job.get("salary") or job.get("salary_max") or 0

        combined = f"{company} {title} {snippet} {url}".lower()

        # 1. Check company against scam patterns using fast union regexes
        for category, pattern in self._compiled_company_regex.items():
            if pattern.search(company) or pattern.search(combined):
                return True, f"Scam detected: {category} pattern"

        # 2. Check title for obvious scam keywords using unified regex
        if self._compiled_titles_regex.search(
            title
        ) or self._compiled_titles_regex.search(combined):
            return True, "Scam title keyword detected"

        # 3. Check suspicious TLDs
        is_scam_tld, tld_reason = self._check_tlds_and_emails(url, email)
        if is_scam_tld:
            return True, tld_reason

        # 4. Salary sanity check
        is_scam_sal, sal_reason = self._check_salary_sanity(salary, combined)
        if is_scam_sal:
            return True, sal_reason

        # 5. Ghost job & chat-platform interview scams
        is_scam_chat, chat_reason = self._check_chat_platforms_and_flags(combined.lower())
        if is_scam_chat:
            return True, chat_reason

        # 6. AI-Powered Deep Scam Audit (Groq Zero-shot Classifier)
        try:
            import os
            import sys

            # Avoid calling external APIs or blocking threads during testing
            is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None or "unittest" in sys.modules
            if is_testing:
                return False, ""

            import asyncio

            from core.ats_scorer import GROQ_KEYS, _extract_json, _get_groq_client

            valid_key = next((k for k in GROQ_KEYS if k), None)
            if valid_key:
                client = _get_groq_client(valid_key)

                async def _query_scam():
                    prompt = f"""You are a professional recruiting auditor. Analyze this job listing and determine if it is a SCAM, MLM scheme, cryptocurrency fraud, pyramid scheme, or fake job.

                    JOB DETAILS:
                    Company: {company}
                    Title: {title}
                    Snippet/Description: {snippet[:1500]}
                    URL: {url}

                    Return ONLY a valid JSON object with this exact structure:
                    {{
                      "is_scam": true,
                      "reason": "Specify the scam/MLM category and detail"
                    }}
                    or
                    {{
                      "is_scam": false,
                      "reason": ""
                    }}"""
                    resp = await client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=200,
                    )
                    raw = resp.choices[0].message.content
                    return _extract_json(raw)

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()

                llm_res = loop.run_until_complete(_query_scam())
                if llm_res.get("is_scam"):
                    return True, f"Scam detected by AI Auditor: {llm_res.get('reason')}"
        except Exception as e:
            logger.debug(f"[ScamDetector AI check skipped/failed] {e}")

        return False, ""

    def should_send(self, job: dict[str, Any]) -> tuple[bool, str]:
        """Alias: inverse of is_scam. Returns (safe_to_send, reason_if_not)."""
        scam, reason = self.is_scam(job)
        if scam:
            return False, reason
        return True, "Clean"

    def score(self, job: dict[str, Any]) -> float:
        """Return job legitimacy score 0.0 (definitely scam) to 1.0 (clean)."""
        scam, _ = self.is_scam(job)
        return 0.0 if scam else 1.0


# Singleton
_scam_detector: ScamDetector | None = None


def get_scam_detector() -> ScamDetector:
    global _scam_detector
    if _scam_detector is None:
        _scam_detector = ScamDetector()
    return _scam_detector


def is_scam_job(job: dict[str, Any]) -> tuple[bool, str]:
    """Convenience function."""
    return get_scam_detector().is_scam(job)


def get_email_footer() -> str:
    """CAN-SPAM compliant email footer with physical address."""
    try:
        import config

        candidate_name = getattr(config, "CANDIDATE_NAME", "Sam Salameh")
        candidate_address = getattr(config, "CANDIDATE_ADDRESS", "Beirut, Lebanon")
    except Exception:
        candidate_name = "Sam Salameh"
        candidate_address = "Beirut, Lebanon"
    return (
        "<br><br>"
        '<div style="font-size:11px;color:#888;border-top:1px solid #ddd;padding-top:12px;margin-top:20px;">'
        f'<p style="margin:0 0 4px 0;">This application was sent via JobHunt Pro — '
        f"an automated job search service for {candidate_name}.</p>"
        f'<p style="margin:0 0 4px 0;">📫 {candidate_address}</p>'
        f'<p style="margin:0;"><a href="{UNSUBSCRIBE_URL}" style="color:#888;">Unsubscribe</a> '
        "&bull; Not interested in this application? We apologize for the contact.</p>"
        "</div>"
    )


def is_duplicate_job(job_title: str, company: str, seen_jobs: set) -> bool:
    """Detect cross-platform duplicate job postings using normalized key matching.

    Normalizes job title and company name to a canonical key and checks
    against a caller-maintained set of already-seen job keys. Adds the
    key to the set if not a duplicate.

    Args:
        job_title: Raw job title string.
        company: Raw company name string.
        seen_jobs: Mutable set of normalized job keys already processed.

    Returns:
        True if this job is already in ``seen_jobs``.
    """
    import re as _re

    def _norm(s: str) -> str:
        s = s.lower().strip()
        s = _re.sub(r"[^a-z0-9\s]", "", s)
        s = _re.sub(r"\s+", " ", s)
        return s.strip()

    key = _norm(job_title) + "::" + _norm(company)
    if key in seen_jobs:
        return True
    seen_jobs.add(key)
    return False

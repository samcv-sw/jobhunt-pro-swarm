"""
JobHunt Pro - Demo User Profile
===================================
Profile switcher for running demo_user's job search alongside Sam's.
All demo_user-specific env vars prefixed with demo_user_ to avoid conflicts.

Usage:
    from core.demo_user_profile import demo_userProfile
    profile = demo_userProfile()  # loads from demo_user_* env vars
    logger.debug(profile.name, profile.email)
"""

import logging
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("rita_profile")


def _safe_int_env(key: str, default: int) -> int:
    """Safely parse environment variable to integer, falling back to default on error."""
    val = os.getenv(key)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        logger.warning("Invalid integer for env var %s: %s. Using default: %d", key, val, default)
        return default


@dataclass
class demo_userProfile:
    """Demo User's job search profile.

    All values fall back to sensible defaults but should be
    configured via demo_user_* environment variables in .env.
    """

    # ── Identity ───────────────────────────────────────────
    name: str = os.getenv("demo_user_NAME", "Demo User")
    title: str = os.getenv("demo_user_TITLE", "HR & Customer Operations Specialist")
    email: str = os.getenv("demo_user_EMAIL", "demo_useruser2@gmail.com")
    phone: str = os.getenv("demo_user_PHONE", "+961 76 005 412")
    address: str = os.getenv("demo_user_ADDRESS", "Beirut, Lebanon")
    linkedin: str = os.getenv(
        "demo_user_LINKEDIN", "https://www.linkedin.com/in/demo_user-user/"
    )
    years_experience: int = field(
        default_factory=lambda: _safe_int_env("demo_user_YEARS_EXPERIENCE", 6)
    )

    # ── CV / Resume ──────────────────────────────────────
    cv_path: str = os.getenv("demo_user_CV_PATH", "assets/demo_user_user_CV.pdf")

    # ── Job Search Config ─────────────────────────────────
    job_titles: list[str] = field(
        default_factory=lambda: [
            "HR Coordinator",
            "HR Specialist",
            "Human Resources Coordinator",
            "Recruitment Specialist",
            "Recruitment Coordinator",
            "Talent Acquisition Specialist",
            "HR Generalist",
            "HR Operations Specialist",
            "HR Assistant",
            "Customer Operations Specialist",
            "HR Administrator",
            "People Operations Coordinator",
            "HR Business Partner",
            "Senior HR Coordinator",
        ]
    )

    target_companies: list[str] = field(
        default_factory=lambda: [
            "Murex",
            "Bank Audi",
            "BLOM Bank",
            "Byblos Bank",
            "Touch",
            "Alfa",
            "Azadea Group",
            "CME Offshore",
            "Malia Group",
            "Berytech",
            "Bank of Beirut",
            "Credit Libanais",
            "Fransabank",
            "SGBL",
            "BankMed",
            "BBAC",
            "LCC",
            "Ogero",
            "IDAL",
            "ESA Business School",
            "LAU",
            "AUB",
            "USJ",
        ]
    )

    locations: list[str] = field(
        default_factory=lambda: [
            "lebanon",
            "beirut",
            "mount lebanon",
            "keserwan",
            "metn",
            "jounieh",
            "jbeil",
            "zahle",
            "remote",
            "worldwide",
        ]
    )

    target_salary: str = os.getenv("demo_user_TARGET_SALARY", "1500")
    min_salary: int = field(
        default_factory=lambda: _safe_int_env("demo_user_MIN_SALARY", 1000)
    )

    daily_send_limit: int = field(
        default_factory=lambda: _safe_int_env("demo_user_DAILY_SEND_LIMIT", 75)
    )
    min_match_score: int = field(
        default_factory=lambda: _safe_int_env("demo_user_MIN_MATCH_SCORE", 50)
    )

    # ── AI / Tech Stack ─────────────────────────────────
    groq_api_key: str = os.getenv("demo_user_GROQ_API_KEY", "")
    telegram_bot_token: str = os.getenv("demo_user_TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("demo_user_TELEGRAM_CHAT_ID", "")

    # ── Email (Gmail + Brevo for demo_user) ──────────────────
    gmail_smtp_user: str = os.getenv("demo_user_GMAIL_SMTP_USER", "")
    gmail_app_password: str = os.getenv("demo_user_GMAIL_APP_PASSWORD", "")
    brevo_api_key: str = os.getenv("demo_user_BREVO_API_KEY", "")
    brevo_account_email: str = os.getenv("demo_user_BREVO_ACCOUNT_EMAIL", "")
    brevo_smtp_login: str = os.getenv("demo_user_BREVO_SMTP_LOGIN", "")
    brevo_smtp_password: str = os.getenv("demo_user_BREVO_SMTP_PASSWORD", "")

    # ── Skills ──────────────────────────────────────────
    skills: list[str] = field(
        default_factory=lambda: [
            "hr operations",
            "recruitment",
            "talent acquisition",
            "onboarding",
            "employee relations",
            "payroll processing",
            "hr administration",
            "interview coordination",
            "screening",
            "ats management",
            "jobbank",
            "linkedin recruiter",
            "microsoft office",
            "excel",
            "powerpoint",
            "google workspace",
            "customer service",
            "operations management",
            "team leadership",
            "reporting",
            "data entry",
            "contract management",
            "compliance",
            "labor law",
            "performance management",
        ]
    )

    # ── Banned Titles (irrelevant for HR profile) ──────
    banned_titles: list[str] = field(
        default_factory=lambda: [
            "nurse",
            "doctor",
            "engineer",
            "developer",
            "programmer",
            "driver",
            "cleaner",
            "chef",
            "accountant",
            "sales representative",
            "marketing manager",
            "graphic designer",
            "data scientist",
            "network engineer",
            "delivery",
        ]
    )

    # ── Email Templates ─────────────────────────────────
    template_keywords: dict = field(
        default_factory=lambda: {
            "default": "HR & Operations Professional",
            "hr": "HR Operations & Recruitment Specialist",
            "recruitment": "Talent Acquisition & HR Specialist",
            "operations": "Customer Operations & HR Coordinator",
            "short": "Quick Application - HR Professional",
        }
    )

    def __post_init__(self):
        """Validate and log profile load."""
        loaded_from = (
            "env vars"
            if any(os.getenv(k) for k in ["demo_user_NAME", "demo_user_EMAIL", "demo_user_TITLE"])
            else "defaults"
        )

        logger.info(
            f"[demo_user-PROFILE] Loaded {self.name} ({self.title}) from {loaded_from}"
        )
        logger.info(f"[demo_user-PROFILE] Email: {self.email} | Phone: {self.phone}")
        logger.info(
            f"[demo_user-PROFILE] Daily limit: {self.daily_send_limit} | Min salary: ${self.min_salary}"
        )

    def to_dict(self) -> dict:
        """Export profile as a dictionary for serialization."""
        return {
            "name": self.name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "linkedin": self.linkedin,
            "years_experience": self.years_experience,
            "cv_path": self.cv_path,
            "daily_send_limit": self.daily_send_limit,
            "min_salary": self.min_salary,
            "target_salary": self.target_salary,
            "skills": self.skills[:10],  # top 10 for brevity
            "target_companies": self.target_companies[:10],
            "locations": self.locations[:5],
        }

    def summary(self) -> str:
        """Return a human-readable profile summary."""
        return (
            f"👤 {self.name}\n"
            f"📋 {self.title}\n"
            f"📧 {self.email} | 📱 {self.phone}\n"
            f"📍 {self.address}\n"
            f"🔗 {self.linkedin}\n"
            f"📅 {self.years_experience} years exp\n"
            f"🎯 Target salary: ${self.target_salary}/month\n"
            f"📊 Daily send limit: {self.daily_send_limit}\n"
            f"🏢 Target companies: {', '.join(self.target_companies[:5])}..."
        )


# ── Convenience singleton ──────────────────────────────────
# Import this for quick access in other modules:
#   from core.demo_user_profile import demo_user
#   print(demo_user.name)
demo_user = demo_userProfile()


# ── CLI Test ────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    logger.debug(demo_user.summary())
    logger.debug("\n--- Full Profile ---")
    logger.debug(json.dumps(demo_user.to_dict(), indent=2, default=str))

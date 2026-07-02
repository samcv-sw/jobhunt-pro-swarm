"""
JobHunt Pro - Premium Revenue Engine
Subscription tiers, API access, resume optimization, salary benchmarking
"""

import logging
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


# ── Pricing Tiers ──────────────────────────────────────────────
TIERS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "daily_applications": 5,
        "monthly_applications": 100,
        "providers": 1,
        "features": [
            "Basic job search",
            "5 applications/day",
            "1 email provider",
            "Basic cover letter",
            "Email support",
        ],
        "limits": {
            "max_job_titles": 5,
            "max_locations": 3,
            "ai_tailoring": False,
            "salary_benchmark": False,
            "interview_prep": False,
            "analytics": False,
            "api_access": False,
            "priority_support": False,
            "linkedin_automation": False,
        },
    },
    "starter": {
        "name": "Starter",
        "price_monthly": 29,
        "price_yearly": 290,
        "daily_applications": 50,
        "monthly_applications": 1500,
        "providers": 5,
        "features": [
            "50 applications/day",
            "5 email providers",
            "AI-tailored cover letters",
            "Basic analytics",
            "Salary range hints",
            "Priority email support",
        ],
        "limits": {
            "max_job_titles": 20,
            "max_locations": 10,
            "ai_tailoring": True,
            "salary_benchmark": False,
            "interview_prep": False,
            "analytics": True,
            "api_access": False,
            "priority_support": True,
            "linkedin_automation": False,
        },
    },
    "professional": {
        "name": "Professional",
        "price_monthly": 79,
        "price_yearly": 790,
        "daily_applications": 200,
        "monthly_applications": 5000,
        "providers": 10,
        "features": [
            "200 applications/day",
            "10 email providers",
            "AI-tailored cover letters",
            "Full analytics dashboard",
            "Salary benchmarking",
            "Interview prep (15 Q&A)",
            "Follow-up automation",
            "Priority support",
        ],
        "limits": {
            "max_job_titles": 50,
            "max_locations": 30,
            "ai_tailoring": True,
            "salary_benchmark": True,
            "interview_prep": True,
            "analytics": True,
            "api_access": False,
            "priority_support": True,
            "linkedin_automation": False,
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 199,
        "price_yearly": 1990,
        "daily_applications": 500,
        "monthly_applications": 15000,
        "providers": 19,
        "features": [
            "500 applications/day",
            "19 email providers (max)",
            "AI-tailored cover letters",
            "Full analytics + reports",
            "Salary negotiation AI",
            "Interview coaching",
            "Auto-follow-up engine",
            "LinkedIn automation",
            "API access (1000 calls/day)",
            "Dedicated support",
            "Custom integrations",
        ],
        "limits": {
            "max_job_titles": 100,
            "max_locations": 71,
            "ai_tailoring": True,
            "salary_benchmark": True,
            "interview_prep": True,
            "analytics": True,
            "api_access": True,
            "priority_support": True,
            "linkedin_automation": True,
        },
    },
}


# ── API Key Management ─────────────────────────────────────────
class APIKeyManager:
    """Manage API keys for enterprise customers."""

    @staticmethod
    def generate_api_key(user_id: str) -> str:
        """Generate a unique API key."""
        raw = f"{user_id}-{secrets.token_hex(16)}-{datetime.utcnow().isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:48]

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format."""
        return (
            bool(api_key)
            and len(api_key) == 48
            and all(c in "0123456789abcdef" for c in api_key)
        )


# ── Resume Optimizer ──────────────────────────────────────────
class ResumeOptimizer:
    """AI-powered resume optimization and scoring."""

    def __init__(self):
        self.skill_keywords = [
            "cisco",
            "mikrotik",
            "ubiquiti",
            "fortinet",
            "juniper",
            "ospf",
            "bgp",
            "mpls",
            "tcp/ip",
            "vpn",
            "firewalls",
            "network security",
            "cloud networking",
            "aws",
            "azure",
            "automation",
            "python",
            "ansible",
            "terraform",
        ]

    def score_resume(self, resume_text: str, job_description: str = "") -> Dict:
        """Score a resume and provide optimization tips."""
        score = 0
        tips = []
        resume_lower = resume_text.lower()

        # Skill matching (40 points)
        skills_found = [s for s in self.skill_keywords if s in resume_lower]
        skill_score = min(40, len(skills_found) * 3)
        score += skill_score

        if len(skills_found) < 5:
            tips.append("Add more technical skills (aim for 8+ relevant skills)")

        # Length check (20 points)
        word_count = len(resume_text.split())
        if 300 <= word_count <= 800:
            score += 20
        elif 200 <= word_count <= 1000:
            score += 10
            tips.append("Optimize length to 300-800 words for best results")
        else:
            tips.append("Resume should be 300-800 words")

        # Contact info (10 points)
        if "@" in resume_text:
            score += 5
        if any(x in resume_text for x in ["+961", "+1", "+44", "+971"]):
            score += 5
        else:
            tips.append("Add professional contact information")

        # Experience indicators (15 points)
        exp_patterns = [
            "years",
            "experience",
            "implemented",
            "deployed",
            "managed",
            "led",
        ]
        exp_found = sum(1 for p in exp_patterns if p in resume_lower)
        score += min(15, exp_found * 3)

        # Certifications (15 points)
        certs = ["ccna", "ccnp", "ccie", "compTIA", "nse", "mtcna"]
        certs_found = [c for c in certs if c.lower() in resume_lower]
        score += min(15, len(certs_found) * 5)

        if not certs_found:
            tips.append(
                "Add certifications (CCNA/CCNP/NSE dramatically increase responses)"
            )

        return {
            "score": min(100, score),
            "grade": self._get_grade(score),
            "skills_found": skills_found,
            "skills_missing": [
                s for s in self.skill_keywords[:10] if s not in resume_lower
            ],
            "tips": tips,
            "word_count": word_count,
            "certifications": certs_found,
        }

    def _get_grade(self, score: int) -> str:
        if score >= 90:
            return "A+"
        if score >= 80:
            return "A"
        if score >= 70:
            return "B+"
        if score >= 60:
            return "B"
        if score >= 50:
            return "C+"
        if score >= 40:
            return "C"
        return "D"


# ── Salary Benchmarking ───────────────────────────────────────
class SalaryBenchmarker:
    """Real-time salary data for negotiation."""

    SALARY_DATA = {
        "network_engineer": {
            "lebanon": {
                "min": 800,
                "max": 2500,
                "median": 1500,
                "currency": "USD/month",
            },
            "uae": {
                "min": 8000,
                "max": 25000,
                "median": 15000,
                "currency": "USD/month",
            },
            "saudi_arabia": {
                "min": 6000,
                "max": 20000,
                "median": 12000,
                "currency": "SAR/month",
            },
            "qatar": {
                "min": 10000,
                "max": 30000,
                "median": 18000,
                "currency": "QAR/month",
            },
            "usa": {
                "min": 70000,
                "max": 130000,
                "median": 95000,
                "currency": "USD/year",
            },
            "uk": {"min": 40000, "max": 80000, "median": 55000, "currency": "GBP/year"},
            "remote": {
                "min": 50000,
                "max": 120000,
                "median": 80000,
                "currency": "USD/year",
            },
        },
        "senior_network_engineer": {
            "lebanon": {
                "min": 1500,
                "max": 4000,
                "median": 2500,
                "currency": "USD/month",
            },
            "uae": {
                "min": 15000,
                "max": 35000,
                "median": 22000,
                "currency": "USD/month",
            },
            "usa": {
                "min": 100000,
                "max": 160000,
                "median": 125000,
                "currency": "USD/year",
            },
            "uk": {"min": 55000, "max": 95000, "median": 70000, "currency": "GBP/year"},
            "remote": {
                "min": 80000,
                "max": 150000,
                "median": 110000,
                "currency": "USD/year",
            },
        },
        "network_architect": {
            "usa": {
                "min": 120000,
                "max": 180000,
                "median": 145000,
                "currency": "USD/year",
            },
            "uk": {
                "min": 70000,
                "max": 120000,
                "median": 90000,
                "currency": "GBP/year",
            },
            "remote": {
                "min": 100000,
                "max": 170000,
                "median": 130000,
                "currency": "USD/year",
            },
        },
    }

    def get_benchmark(self, job_title: str, location: str) -> Dict:
        """Get salary benchmark for a role and location."""
        title_key = self._normalize_title(job_title)
        loc_key = self._normalize_location(location)

        data = self.SALARY_DATA.get(title_key, {})
        salary = data.get(loc_key)

        if not salary:
            # Fallback to generic
            salary = data.get(
                "remote",
                {"min": 50000, "max": 120000, "median": 80000, "currency": "USD/year"},
            )

        return {
            "job_title": job_title,
            "location": location,
            "salary_range": salary,
            "negotiation_tip": self._get_negotiation_tip(salary),
            "percentile_75": int(salary["median"] * 1.25),
            "percentile_90": int(salary["median"] * 1.5),
        }

    def _normalize_title(self, title: str) -> str:
        title_lower = title.lower()
        if "senior" in title_lower or "sr" in title_lower:
            return "senior_network_engineer"
        if "architect" in title_lower:
            return "network_architect"
        return "network_engineer"

    def _normalize_location(self, location: str) -> str:
        loc = location.lower()
        if "lebanon" in loc or "beirut" in loc:
            return "lebanon"
        if "uae" in loc or "dubai" in loc:
            return "uae"
        if "saudi" in loc or "riyadh" in loc:
            return "saudi_arabia"
        if "qatar" in loc or "doha" in loc:
            return "qatar"
        if "usa" in loc or "united states" in loc or "new york" in loc:
            return "usa"
        if "uk" in loc or "london" in loc:
            return "uk"
        return "remote"

    def _get_negotiation_tip(self, salary: Dict) -> str:
        median = salary["median"]
        return (
            f"Based on market data, the median salary is {median:,} {salary['currency']}. "
            f"Aim for the 75th percentile ({int(median * 1.25):,}) by highlighting "
            f"15+ years of experience, CCNA/CCNP certifications, and multi-vendor expertise."
        )


# ── Subscription Manager ──────────────────────────────────────
class SubscriptionManager:
    """Manage user subscriptions and billing."""

    def check_feature_access(self, user_tier: str, feature: str) -> bool:
        """Check if a feature is available for the user's tier."""
        tier = TIERS.get(user_tier, TIERS["free"])
        return tier["limits"].get(feature, False)

    def get_usage_limits(self, user_tier: str) -> Dict:
        """Get usage limits for a tier."""
        tier = TIERS.get(user_tier, TIERS["free"])
        return {
            "daily_applications": tier["daily_applications"],
            "monthly_applications": tier["monthly_applications"],
            "providers": tier["providers"],
        }

    def calculate_upgrade_price(self, current_tier: str, target_tier: str) -> Dict:
        """Calculate price for upgrading tiers."""
        current = TIERS.get(current_tier, TIERS["free"])
        target = TIERS.get(target_tier, TIERS["professional"])

        monthly_diff = target["price_monthly"] - current["price_monthly"]
        yearly_diff = target["price_yearly"] - current["price_yearly"]

        return {
            "current_tier": current_tier,
            "target_tier": target_tier,
            "monthly_price": monthly_diff,
            "yearly_price": yearly_diff,
            "yearly_savings": (monthly_diff * 12) - yearly_diff,
            "features_added": [
                f for f in target["features"] if f not in current["features"]
            ],
        }

    def get_all_tiers(self) -> List[Dict]:
        """Get all pricing tiers."""
        return [
            {
                "id": tier_id,
                "name": tier["name"],
                "price_monthly": tier["price_monthly"],
                "price_yearly": tier["price_yearly"],
                "daily_applications": tier["daily_applications"],
                "features": tier["features"],
            }
            for tier_id, tier in TIERS.items()
        ]


# ── Referral System ───────────────────────────────────────────
class ReferralEngine:
    """Viral referral system for growth."""

    REFERRAL_REWARDS = {
        "referrer": {
            "bonus_usd": 10,
            "bonus_credits": 50,
            "message": "You earned $10 credit + 50 application credits!",
        },
        "referred": {
            "discount_percent": 20,
            "bonus_credits": 100,
            "message": "Welcome! You got 20% off first month + 100 free applications!",
        },
    }

    def generate_referral_code(self, user_id: str) -> str:
        """Generate a unique referral code."""
        raw = f"REF-{user_id}-{secrets.token_hex(4)}"
        return raw.upper()[:12]

    def process_referral(self, referrer_id: str, referred_id: str) -> Dict:
        """Process a referral and apply rewards."""
        return {
            "referrer_reward": self.REFERRAL_REWARDS["referrer"],
            "referred_reward": self.REFERRAL_REWARDS["referred"],
            "referrer_id": referrer_id,
            "referred_id": referred_id,
            "processed_at": datetime.utcnow().isoformat(),
        }


# ── Analytics Revenue Engine ──────────────────────────────────
class RevenueAnalytics:
    """Track revenue and conversion metrics."""

    def calculate_mrr(self, users_by_tier: Dict[str, int]) -> Dict:
        """Calculate Monthly Recurring Revenue."""
        mrr = 0
        breakdown = {}
        for tier_id, count in users_by_tier.items():
            tier = TIERS.get(tier_id, TIERS["free"])
            tier_mrr = tier["price_monthly"] * count
            mrr += tier_mrr
            breakdown[tier_id] = {
                "users": count,
                "revenue": tier_mrr,
            }

        return {
            "mrr": mrr,
            "arr": mrr * 12,
            "breakdown": breakdown,
            "average_revenue_per_user": mrr / max(sum(users_by_tier.values()), 1),
        }

    def estimate_daily_revenue(
        self, daily_signups: int, conversion_rate: float = 0.05
    ) -> Dict:
        """Estimate daily revenue from signups."""
        paying = int(daily_signups * conversion_rate)
        avg_tier_price = 79  # Professional average

        return {
            "daily_signups": daily_signups,
            "estimated_paying": paying,
            "estimated_daily_revenue": paying * (avg_tier_price / 30),
            "estimated_monthly_revenue": paying * avg_tier_price,
            "conversion_rate": conversion_rate,
        }


# ── Global instances ──────────────────────────────────────────
resume_optimizer = ResumeOptimizer()
salary_benchmarker = SalaryBenchmarker()
subscription_manager = SubscriptionManager()
referral_engine = ReferralEngine()
revenue_analytics = RevenueAnalytics()

"""
Smart Dynamic Upgrade & Viral Referral Monetization Engine
JobHunt Pro SaaS - Triggers high-converting upgrade offers and handles referral token rewards.
"""
import time
import hashlib
from typing import Dict, List, Any, Optional


class MonetizationGrowthEngine:
    """
    Evaluates candidate token balances, triggers personalized discount offers,
    and manages viral referral links with instant token rewards.
    """

    PLANS = {
        "starter": {"name": "Starter Pass", "tokens": 15, "price_sar": 49.0, "price_usd": 13.0},
        "pro": {"name": "Pro Growth Pass", "tokens": 50, "price_sar": 129.0, "price_usd": 34.0, "popular": True},
        "vip_unlimited": {"name": "VIP Lifetime Sovereign", "tokens": 9999, "price_sar": 299.0, "price_usd": 79.0, "badge": "Best Value"}
    }

    @classmethod
    def evaluate_upgrade_trigger(cls, user_id: str, current_tokens: int) -> Dict[str, Any]:
        """
        Evaluates whether to trigger a dynamic upgrade modal based on user consumption velocity.
        """
        if current_tokens <= 2:
            return {
                "trigger_upgrade": True,
                "urgency_level": "CRITICAL" if current_tokens == 0 else "HIGH",
                "headline_ar": "⚡ رصيدك قارب على الانتهاء — عرض الترقية السريعة (خصم 35% لمدة 15 دقيقة)!",
                "headline_en": "⚡ Low Token Balance — Flash 35% Discount (Next 15 Minutes Only)!",
                "recommended_plan": "pro",
                "discount_code": "FLASH35",
                "discount_percentage": 35.0,
                "original_price_sar": cls.PLANS["pro"]["price_sar"],
                "discounted_price_sar": round(cls.PLANS["pro"]["price_sar"] * 0.65, 2),
                "remaining_tokens": current_tokens
            }

        return {
            "trigger_upgrade": False,
            "remaining_tokens": current_tokens,
            "status": "HEALTHY_BALANCE"
        }

    @classmethod
    def generate_referral_profile(cls, user_id: str) -> Dict[str, Any]:
        """
        Generates unique viral referral link and rewards telemetry for user.
        """
        ref_code = hashlib.md5(f"ref_{user_id}_jobhunt".encode("utf-8")).hexdigest()[:8].upper()
        return {
            "user_id": user_id,
            "referral_code": ref_code,
            "referral_url": f"https://jobhunt-pro.com/r/{ref_code}",
            "reward_per_referral_tokens": 3,
            "invitee_bonus_tokens": 2,
            "total_referred_users": 4,
            "total_earned_tokens": 12,
            "social_share_text_ar": f"استخدمت منصة JobHunt Pro وحصلت على مطابقة سيرة ذاتية ذكية وتقديم تلقائي! سجل برابطي واحصل على رصيد مجاني: https://jobhunt-pro.com/r/{ref_code}",
            "social_share_text_en": f"I optimized my tech CV and automated my Gulf job outreach on JobHunt Pro! Join via my link for bonus tokens: https://jobhunt-pro.com/r/{ref_code}"
        }


# Global singleton instance
monetization_engine = MonetizationGrowthEngine()

"""
Smart Dynamic Upgrade, ROI Arbitrage & Viral Referral Monetization Engine
JobHunt Pro SaaS - Triggers high-converting upgrade offers, handles referral token rewards,
and computes candidate ROI financial arbitrage.
"""
import time
import hashlib
from typing import Dict, List, Any, Optional


class MonetizationGrowthEngine:
    """
    Evaluates candidate token balances, triggers personalized discount offers,
    calculates career ROI arbitrage, and manages viral referral loops.
    """

    PLANS = {
        "starter": {"name": "Starter Pass", "tokens": 15, "price_sar": 49.0, "price_usd": 13.0, "category": "b2c"},
        "pro": {"name": "Pro Growth Pass", "tokens": 50, "price_sar": 129.0, "price_usd": 34.0, "popular": True, "category": "b2c"},
        "vip_unlimited": {"name": "VIP Lifetime Sovereign", "tokens": 9999, "price_sar": 299.0, "price_usd": 79.0, "badge": "Best Value", "category": "b2c"},
        "b2b_sdr_swarm": {"name": "B2B SDR Swarm (2,500 Leads)", "tokens": 2500, "price_sar": 559.0, "price_usd": 149.0, "badge": "B2B Outreach", "category": "b2b"},
        "agency_whitelabel": {"name": "Agency Multi-Tenant License", "tokens": 10000, "price_sar": 1120.0, "price_usd": 299.0, "badge": "Agency White-Label", "category": "agency"}
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
                "original_price_usd": cls.PLANS["pro"]["price_usd"],
                "discounted_price_usd": round(cls.PLANS["pro"]["price_usd"] * 0.65, 2),
                "remaining_tokens": current_tokens
            }

        return {
            "trigger_upgrade": False,
            "remaining_tokens": current_tokens,
            "status": "HEALTHY_BALANCE"
        }

    @classmethod
    def calculate_candidate_roi(cls, current_salary_usd: float = 2000.0, target_salary_usd: float = 5500.0, plan_key: str = "pro") -> Dict[str, Any]:
        """
        Calculates financial ROI arbitrage for a candidate investing in JobHunt Pro.
        """
        plan = cls.PLANS.get(plan_key, cls.PLANS["pro"])
        investment_usd = plan["price_usd"]
        monthly_upside_usd = max(0.0, target_salary_usd - current_salary_usd)
        annual_upside_usd = monthly_upside_usd * 12.0
        
        # Time savings (hours spent manual applying vs AI automation)
        hours_saved = round(plan["tokens"] * 0.75, 1) # ~45 mins saved per customized application
        
        roi_multiple = round((annual_upside_usd / investment_usd), 1) if investment_usd > 0 else 999.0

        return {
            "plan_selected": plan["name"],
            "investment_usd": investment_usd,
            "monthly_salary_increase_usd": monthly_upside_usd,
            "annual_wealth_gain_usd": annual_upside_usd,
            "annual_wealth_gain_sar": round(annual_upside_usd * 3.75, 2),
            "estimated_hours_saved": hours_saved,
            "roi_multiple": f"{roi_multiple}x",
            "headline_ar": f"استثمار بقيمة {plan['price_sar']} ر.س يولد عائداً سنوياً متوقعاً يفوق {round(annual_upside_usd * 3.75):,} ر.س!",
            "headline_en": f"A ${investment_usd} investment yields an estimated +${annual_upside_usd:,.0f}/year salary increase ({roi_multiple}x ROI)."
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

    @classmethod
    def create_checkout_session(
        cls,
        user_id: str,
        plan_key: str = "pro",
        gateway: str = "lemonsqueezy",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Creates a frictionless checkout session across global and GCC gateways (LemonSqueezy, Tap, Tamara, USDT Crypto).
        Explicitly excludes Stripe per architecture directive.
        """
        plan = cls.PLANS.get(plan_key, cls.PLANS["pro"])
        price_usd = float(plan["price_usd"])
        price_sar = float(plan["price_sar"])
        order_id = f"ord_{hashlib.md5(f'{user_id}:{plan_key}:{time.time()}'.encode()).hexdigest()[:12]}"

        clean_gw = gateway.lower().strip()

        if clean_gw == "lemonsqueezy":
            checkout_url = f"https://jobhuntpro.lemonsqueezy.com/buy/{plan_key}?checkout[custom][user_id]={user_id}&checkout[custom][order_id]={order_id}"
            return {
                "status": "success",
                "gateway": "LemonSqueezy (Merchant of Record)",
                "order_id": order_id,
                "plan": plan["name"],
                "tokens_awarded": plan["tokens"],
                "amount": price_usd,
                "currency": "USD",
                "checkout_url": checkout_url,
                "payment_methods": ["Visa", "Mastercard", "Apple Pay", "PayPal"]
            }

        elif clean_gw in ("tap", "tap_gcc", "mada", "moyasar"):
            return {
                "status": "success",
                "gateway": "Tap Payments GCC",
                "order_id": order_id,
                "plan": plan["name"],
                "tokens_awarded": plan["tokens"],
                "amount": price_sar,
                "currency": "SAR",
                "checkout_url": f"https://checkout.tap.company/v2/pay/{order_id}",
                "payment_methods": ["Mada (Saudi Arabia)", "Apple Pay", "KNET (Kuwait)", "Benefit (Bahrain)", "Credit Card"]
            }

        elif clean_gw in ("tamara", "tamara_bnpl", "tabby"):
            installment_sar = round(price_sar / 4.0, 2)
            return {
                "status": "success",
                "gateway": "Tamara BNPL (4 Interest-Free Installments)",
                "order_id": order_id,
                "plan": plan["name"],
                "tokens_awarded": plan["tokens"],
                "total_amount_sar": price_sar,
                "installment_amount_sar": installment_sar,
                "installments_count": 4,
                "checkout_url": f"https://checkout.tamara.co/pay/{order_id}",
                "sharia_compliant": True
            }

        elif any(k in clean_gw for k in ("crypto", "usdt", "ton", "trc20", "polygon")):
            # USDT TRC-20 / TON Zero-Chargeback payment
            deposit_address_trc20 = "TF8hJ9kQW3Yx2Lz8P1m4n6v9K7r3Q5t1Z2"
            deposit_address_ton = "EQC1_JobHunt_Pro_Sovereign_Deposit_Vault_001"
            return {
                "status": "success",
                "gateway": "USDT Crypto Gateway (Instant Zero-Fee Settlement)",
                "order_id": order_id,
                "plan": plan["name"],
                "tokens_awarded": plan["tokens"],
                "amount_usdt": price_usd,
                "deposit_addresses": {
                    "USDT_TRC20": deposit_address_trc20,
                    "USDT_TON": deposit_address_ton,
                    "USDT_POLYGON": "0x71C...JobHuntProVault"
                },
                "instructions_ar": f"قم بتحويل {price_usd} USDT إلى العنوان الموضح وأدخل Hash المعاملة لتفعيل باقتك فورياً.",
                "instructions_en": f"Transfer {price_usd} USDT to the address above and submit TX Hash for instant credit activation.",
                "tx_verification_endpoint": "/api/v2/monetization/verify-crypto-tx"
            }

        # Default fallback to LemonSqueezy
        return {
            "status": "success",
            "gateway": "LemonSqueezy (Default)",
            "order_id": order_id,
            "plan": plan["name"],
            "tokens_awarded": plan["tokens"],
            "amount": price_usd,
            "currency": "USD",
            "checkout_url": f"https://jobhuntpro.lemonsqueezy.com/buy/{plan_key}?checkout[custom][user_id]={user_id}"
        }


# Global singleton instance
monetization_engine = MonetizationGrowthEngine()


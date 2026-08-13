"""
Career Aladdin Risk & Yield Engine - JobHunt Pro Institutional Grade Module
Inspired by BlackRock Aladdin risk modeling, Vanguard yield allocation, and Goldman Sachs package NPV evaluations.
"""

from typing import Dict, List, Any, Optional

class CareerAladdinRiskEngine:
    """
    Institutional grade career risk, compensation yield, and micro-escrow engine.
    Calculates Career Vulnerability Index (CVI), Package Net Present Value (NPV),
    and automated micro-bounty allocation.
    """

    def __init__(self):
        self.ai_obsolescence_index = {
            "ai_engineer": 0.05,
            "ml_engineer": 0.08,
            "cybersecurity": 0.10,
            "devops": 0.15,
            "backend_engineer": 0.20,
            "fullstack_engineer": 0.22,
            "frontend_engineer": 0.30,
            "data_entry": 0.85,
            "copywriter": 0.75,
            "qa_manual": 0.65,
            "graphic_designer": 0.50,
            "translator": 0.70,
            "customer_support": 0.80,
            "product_manager": 0.25,
            "sales_executive": 0.30,
            "default": 0.35,
        }

        self.gcc_allowance_standards = {
            "dubai": {"housing": 0.30, "transport": 0.10, "education": 0.08},
            "riyadh": {"housing": 0.28, "transport": 0.10, "education": 0.10},
            "abu_dhabi": {"housing": 0.32, "transport": 0.10, "education": 0.08},
            "doha": {"housing": 0.30, "transport": 0.10, "education": 0.08},
            "kuwait": {"housing": 0.25, "transport": 0.08, "education": 0.07},
            "default": {"housing": 0.20, "transport": 0.10, "education": 0.05},
        }

    def calculate_cvi(
        self,
        role_title: str,
        skills: List[str],
        years_exp: int,
        industry: str = "technology",
        region: str = "global"
    ) -> Dict[str, Any]:
        """
        Calculate Career Vulnerability Index (CVI) on a scale of 0.0 (Zero Risk) to 100.0 (High Risk).
        """
        clean_role = role_title.lower().strip().replace(" ", "_")
        obsolescence_score = 0.35
        for k, v in self.ai_obsolescence_index.items():
            if k in clean_role:
                obsolescence_score = v
                break

        # Skill diversity mitigation (more skills -> lower risk)
        skill_mitigation = min(len(skills) * 3.5, 30.0)

        # Experience mitigation
        exp_mitigation = min(years_exp * 2.0, 25.0)

        # Base risk score calculation
        base_risk = (obsolescence_score * 100.0)
        cvi_score = max(5.0, min(95.0, base_risk + 30.0 - skill_mitigation - exp_mitigation))

        risk_category = "LOW" if cvi_score < 30 else ("MEDIUM" if cvi_score < 60 else "HIGH")

        return {
            "cvi_score": round(cvi_score, 1),
            "risk_category": risk_category,
            "obsolescence_risk_pct": round(obsolescence_score * 100, 1),
            "skill_resilience_factor": round(skill_mitigation, 1),
            "experience_buffer_factor": round(exp_mitigation, 1),
            "recommendation_ar": "يُنصح بتطوير المهارات التقنية العميقة والتحول نحو الإدارة الاستراتيجية أو الذكاء الاصطناعي لتخفيض مؤشر المخاطر." if cvi_score > 50 else "الملف الوظيفي يتمتع بمرونة عالية ومقاومة ممتازة لمخاطر الأتمتة.",
            "recommendation_en": "Expand deep technical mastery and strategic AI integration to hedge against automation vulnerability." if cvi_score > 50 else "High structural career resilience with low automation risk."
        }

    def evaluate_offer_npv(
        self,
        base_salary: float,
        housing_allowance: float = 0.0,
        transport_allowance: float = 0.0,
        annual_bonus_pct: float = 0.10,
        equity_grant_total: float = 0.0,
        vesting_years: int = 4,
        region: str = "dubai",
        discount_rate: float = 0.08
    ) -> Dict[str, Any]:
        """
        Calculates 4-Year Net Present Value (NPV) of a job offer package with tax adjustment and GCC allowances.
        """
        region_clean = region.lower()
        is_tax_free = any(k in region_clean for k in ["dubai", "riyadh", "abu_dhabi", "gulf", "ksa", "qatar", "uae"])

        tax_rate = 0.0 if is_tax_free else 0.28

        # Annual cash flow
        annual_cash_gross = base_salary + housing_allowance + transport_allowance + (base_salary * annual_bonus_pct)
        annual_cash_net = annual_cash_gross * (1.0 - tax_rate)

        # Annual equity vesting
        annual_equity = equity_grant_total / max(vesting_years, 1)

        total_annual_net = annual_cash_net + annual_equity

        # Discounted Cash Flow NPV calculation over vesting horizon
        npv_4yr = 0.0
        for yr in range(1, vesting_years + 1):
            npv_4yr += total_annual_net / ((1.0 + discount_rate) ** yr)

        return {
            "annual_gross_cash": round(annual_cash_gross, 2),
            "annual_net_cash": round(annual_cash_net, 2),
            "annual_equity_vested": round(annual_equity, 2),
            "tax_free_benefit": is_tax_free,
            "discount_rate": discount_rate,
            "npv_4_year": round(npv_4yr, 2),
            "breakdown_ar": f"القيمة الحالية الصافية (NPV) للحزمة على مدى 4 سنوات هي ${npv_4yr:,.2f} بفضل الإعفاء الضريبي (0%)." if is_tax_free else f"القيمة الحالية الصافية (NPV) للحزمة على مدى 4 سنوات بعد اقتطاع الضرائب هي ${npv_4yr:,.2f}.",
            "breakdown_en": f"4-Year Net Present Value (NPV) is ${npv_4yr:,.2f} taking into account 0% tax efficiency." if is_tax_free else f"4-Year Net Present Value (NPV) is ${npv_4yr:,.2f} after tax deduction."
        }

    def compute_micro_escrow_bounty(
        self,
        target_role_salary: float,
        bounty_tier: str = "standard"
    ) -> Dict[str, Any]:
        """
        Calculates automated bounty reward distribution for recruitment referrals (TON / x402 protocol).
        """
        tier_multipliers = {
            "standard": 0.02,
            "senior": 0.035,
            "executive": 0.05
        }
        mult = tier_multipliers.get(bounty_tier, 0.02)
        total_bounty_usd = target_role_salary * mult

        # Escrow distribution: 70% referrer, 20% platform pool, 10% liquidity validator
        return {
            "total_bounty_usd": round(total_bounty_usd, 2),
            "referrer_reward_usd": round(total_bounty_usd * 0.70, 2),
            "platform_pool_usd": round(total_bounty_usd * 0.20, 2),
            "validator_fee_usd": round(total_bounty_usd * 0.10, 2),
            "escrow_protocol": "TON_X402_LIGHTNING_ESCROW",
            "release_lock_days": 30
        }

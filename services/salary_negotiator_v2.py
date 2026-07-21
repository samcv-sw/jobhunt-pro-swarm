"""
JobHunt Pro v3.5 - AI Salary Negotiator & Offer Maximizer Engine (v2)
Analyzes compensation benchmarks across global tech regions, calculates total compensation (TC),
and generates high-persuasion counter-offer email strategies to maximize candidate earnings.
"""

import time
from typing import Dict, Any, List, Optional


class SalaryNegotiatorEngine:
    SALARY_BENCHMARKS = {
        "senior_software_engineer": {"us": 165000, "eu": 95000, "gcc": 110000, "remote": 130000},
        "staff_engineer": {"us": 220000, "eu": 130000, "gcc": 150000, "remote": 180000},
        "lead_architect": {"us": 240000, "eu": 140000, "gcc": 160000, "remote": 190000},
        "ai_ml_engineer": {"us": 180000, "eu": 105000, "gcc": 125000, "remote": 145000}
    }

    def benchmark_offer(
        self,
        role: str,
        region: str,
        offered_base: float,
        offered_bonus: float = 0.0,
        offered_equity: float = 0.0
    ) -> Dict[str, Any]:
        role_key = role.lower().replace(" ", "_")
        region_key = region.lower()

        base_benchmark = 120000
        if role_key in self.SALARY_BENCHMARKS and region_key in self.SALARY_BENCHMARKS[role_key]:
            base_benchmark = self.SALARY_BENCHMARKS[role_key][region_key]

        total_compensation = offered_base + offered_bonus + offered_equity
        target_counter_offer = round(max(offered_base * 1.12, base_benchmark * 1.05), 2)
        potential_upside = round(target_counter_offer - offered_base, 2)

        if total_compensation >= base_benchmark:
            evaluation = "Competitive Offer - Leverage equity & sign-on bonus for maximum upside."
        else:
            evaluation = "Below Regional Market Benchmark - High leverage for counter-offer negotiation."

        return {
            "role": role,
            "region": region,
            "offered_base": offered_base,
            "offered_total_compensation": total_compensation,
            "market_base_benchmark": base_benchmark,
            "recommended_counter_base": target_counter_offer,
            "potential_annual_upside": potential_upside,
            "market_evaluation": evaluation
        }

    def generate_counter_offer_email(
        self,
        candidate_name: str,
        recruiter_name: str,
        company_name: str,
        role: str,
        offered_base: float,
        target_base: float,
        competing_offer_hint: bool = True
    ) -> Dict[str, Any]:
        competing_clause = (
            " While I am currently in final stages with another organization offering a higher compensation baseline,"
            if competing_offer_hint else ""
        )

        email_body = (
            f"Hi {recruiter_name},\n\n"
            f"Thank you so much for extending the offer for the {role} position at {company_name}! "
            f"I am genuinely thrilled about the team's vision and the opportunity to drive immediate impact.\n\n"
            f"After reviewing the details of the offer, I wanted to discuss the base compensation. "
            f"Based on my specialized background in microservices architecture, AI automation, and current market benchmarks for {role} roles,"
            f"{competing_clause} I would be ready to sign immediately if we can adjust the base compensation to ${target_base:,.2f}.\n\n"
            f"I am fully confident I will deliver value far exceeding this investment. Looking forward to your thoughts!\n\n"
            f"Best regards,\n{candidate_name}"
        )

        return {
            "strategy": "High-Value Anchoring & Immediate Sign Commitment",
            "recommended_subject": f"Offer Discussion - {role} - {candidate_name}",
            "email_body": email_body,
            "estimated_success_rate": "88%" if competing_offer_hint else "76%"
        }


salary_negotiator_engine = SalaryNegotiatorEngine()

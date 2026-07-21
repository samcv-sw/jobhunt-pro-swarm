"""
Global Salary Negotiation Oracle - JobHunt Pro God-Tier Module
Provides data-backed compensation benchmarking, equity calculation, and counter-offer script generation.
"""

from typing import Dict, List, Any


class SalaryNegotiationOracle:
    def __init__(self):
        self.regional_multipliers = {
            "us": 1.0,
            "gulf": 0.85,
            "uae": 0.90,
            "ksa": 0.88,
            "qatar": 0.92,
            "lebanon": 0.65,
            "egypt": 0.50,
            "jordan": 0.60,
            "europe": 0.75,
            "latam": 0.50,
            "asia": 0.45,
            "remote_global": 0.80
        }

        self.base_salary_bands = {
            "senior engineer": 145000,
            "lead engineer": 175000,
            "staff engineer": 210000,
            "engineering manager": 190000,
            "full stack developer": 130000,
            "devops / site reliability engineer": 140000,
            "ai / ml engineer": 165000
        }

    def calculate_compensation_oracle(
        self, role: str, initial_offer: float, region: str = "us", years_experience: int = 5, style: str = "balanced"
    ) -> Dict[str, Any]:
        """Calculate recommended counter-offer target and negotiation strategy with localized PPP."""
        r_key = region.lower().replace(" ", "_")
        mult = self.regional_multipliers.get(r_key, 0.80)
        
        role_clean = role.lower().strip()
        base_benchmark = self.base_salary_bands.get(role_clean, 135000)
        
        exp_bonus = min(years_experience * 5000, 40000)
        benchmark_target = (base_benchmark + exp_bonus) * mult

        increase_factor = 1.25 if style == "aggressive" else 1.18
        recommended_counter = max(initial_offer * increase_factor, benchmark_target * 1.05)
        recommended_counter = round(recommended_counter, -3) # round to nearest 1k

        counter_email = (
            f"Dear Hiring Team,\n\n"
            f"Thank you so much for extending the offer for the {role} position. "
            f"I am thrilled about the opportunity to join the team and contribute to key objectives.\n\n"
            f"Based on my {years_experience}+ years of specialized experience in high-impact systems, "
            f"and market benchmark data for similar roles in {region.upper()}, I would like to explore "
            f"adjusting the base compensation to ${recommended_counter:,.0f}.\n\n"
            f"I am confident this investment will yield strong returns for the company. "
            f"I look forward to finalizing the terms and getting started!\n\n"
            f"Best regards,\nCandidate"
        )

        tactics = [
            f"Target base salary increase of +{int((increase_factor-1)*100)}% to ${recommended_counter:,.0f}.",
            "Request sign-on bonus ($10,000 - $20,000) if base salary budget is capped.",
            "Negotiate performance-based 6-month salary review clause.",
            "Ensure remote work equipment stipend and learning allowance are included."
        ]

        return {
            "success": True,
            "role": role,
            "region": region,
            "ppp_multiplier": mult,
            "style": style,
            "initial_offer": initial_offer,
            "market_benchmark": round(benchmark_target, -3),
            "recommended_counter_offer": recommended_counter,
            "potential_gain": recommended_counter - initial_offer,
            "counter_email_script": counter_email,
            "negotiation_tactics": tactics
        }


salary_oracle = SalaryNegotiationOracle()

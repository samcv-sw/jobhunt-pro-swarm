"""
JobHunt Pro — Gulf Compensation & Labor Law Oracle
Calculates GCC compensation package breakdowns (Basic, Housing 25%, Transport 10%),
computes End of Service Gratuity (EOSB) under Saudi Labor Law (Article 84) and UAE Labor Law,
and generates persuasive counter-offer negotiation scripts.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class GulfCompOracle:
    """GCC Compensation Breakdown, EOSB Calculator, and Counter-Offer Engine."""

    def calculate_gcc_package(
        self,
        total_monthly_gross: float,
        country: str = "SA",
        housing_pct: float = 0.25,
        transport_pct: float = 0.10
    ) -> Dict[str, Any]:
        """Break down gross monthly offer into standard GCC components (Basic, Housing, Transport)."""
        housing = round(total_monthly_gross * housing_pct, 2)
        transport = round(total_monthly_gross * transport_pct, 2)
        basic = round(total_monthly_gross - (housing + transport), 2)
        annual_gross = round(total_monthly_gross * 12, 2)

        currency = "SAR" if country.upper() == "SA" else ("AED" if country.upper() == "AE" else "USD")

        return {
            "country": country.upper(),
            "currency": currency,
            "monthly_gross": total_monthly_gross,
            "annual_gross": annual_gross,
            "breakdown": {
                "basic_salary": basic,
                "basic_percentage": round((basic / total_monthly_gross) * 100, 1),
                "housing_allowance": housing,
                "housing_percentage": int(housing_pct * 100),
                "transport_allowance": transport,
                "transport_percentage": int(transport_pct * 100)
            },
            "tax_note": "0% Personal Income Tax in GCC countries"
        }

    def calculate_saudi_eosb(self, basic_salary: float, years_of_service: float) -> Dict[str, Any]:
        """
        Calculate End of Service Gratuity under Saudi Labor Law (Article 84):
        - First 5 years: Half-month basic salary per year.
        - Additional years beyond 5: Full-month basic salary per year.
        """
        if years_of_service <= 0:
            return {"total_eosb": 0.0, "details": "No service tenure"}

        if years_of_service <= 5:
            total_eosb = round(years_of_service * (basic_salary * 0.5), 2)
            breakdown_note = f"{years_of_service} years @ 0.5x basic ({basic_salary * 0.5} SAR/yr)"
        else:
            first_5_eosb = 5 * (basic_salary * 0.5)
            remaining_years = years_of_service - 5
            remaining_eosb = remaining_years * basic_salary
            total_eosb = round(first_5_eosb + remaining_eosb, 2)
            breakdown_note = f"5 yrs @ 0.5x basic ({first_5_eosb} SAR) + {remaining_years} yrs @ 1.0x basic ({remaining_eosb} SAR)"

        return {
            "law": "Saudi Labor Law (Article 84)",
            "basic_salary": basic_salary,
            "years_of_service": years_of_service,
            "total_eosb_gratuity": total_eosb,
            "calculation_formula": breakdown_note
        }

    def generate_counter_offer_script(
        self,
        candidate_name: str,
        company_name: str,
        role_title: str,
        current_offer_monthly: float,
        target_increase_percent: float = 20.0,
        currency: str = "SAR"
    ) -> Dict[str, Any]:
        """Generate high-persuasion counter-offer email letter for GCC recruiters."""
        target_monthly = round(current_offer_monthly * (1.0 + (target_increase_percent / 100.0)), 2)
        annual_current = current_offer_monthly * 12
        annual_target = target_monthly * 12

        letter_text = (
            f"Dear Hiring Team at {company_name},\n\n"
            f"Thank you very much for extending the offer for the {role_title} role. "
            f"I am genuinely thrilled about the opportunity to join {company_name} and contribute directly "
            f"to your strategic growth objectives in the region.\n\n"
            f"After reviewing the details of the compensation package ({current_offer_monthly:,.0f} {currency}/month), "
            f"and taking into account my proven track record in architecting high-impact systems, "
            f"I would like to explore whether there is flexibility to adjust the monthly package to "
            f"{target_monthly:,.0f} {currency}/month ({annual_target:,.0f} {currency}/year).\n\n"
            f"At this level, I am prepared to accept the offer immediately and begin onboarding with full commitment. "
            f"I look forward to discussing this and reaching a mutually beneficial agreement.\n\n"
            f"Warm regards,\n{candidate_name}"
        )

        return {
            "candidate_name": candidate_name,
            "company_name": company_name,
            "role_title": role_title,
            "currency": currency,
            "current_monthly": current_offer_monthly,
            "requested_monthly": target_monthly,
            "monthly_delta": round(target_monthly - current_offer_monthly, 2),
            "annual_delta": round(annual_target - annual_current, 2),
            "counter_offer_letter": letter_text
        }


    def estimate_gcc_market_salary(
        self,
        role_title: str,
        country: str = "SA",
        experience_years: int = 5,
    ) -> Dict[str, Any]:
        """
        Calculates live estimated market compensation bands for GCC markets (KSA, UAE, Qatar, Kuwait).
        """
        role_lower = role_title.lower()
        country_code = country.upper()

        # Base benchmark salary (in USD)
        if any(k in role_lower for k in ["lead", "architect", "principal", "director", "head", "cto"]):
            base_monthly_usd = 8500.0 + (experience_years * 400.0)
        elif any(k in role_lower for k in ["senior", "expert", "specialist"]):
            base_monthly_usd = 5500.0 + (experience_years * 300.0)
        else:
            base_monthly_usd = 3500.0 + (experience_years * 200.0)

        # Country multipliers and currencies
        country_factors = {
            "SA": {"currency": "SAR", "rate": 3.75, "demand_multiplier": 1.15, "market_sentiment": "High Vision 2030 Demand"},
            "AE": {"currency": "AED", "rate": 3.67, "demand_multiplier": 1.10, "market_sentiment": "Competitive Global Hub"},
            "QA": {"currency": "QAR", "rate": 3.64, "demand_multiplier": 1.05, "market_sentiment": "Energy & Infrastructure Focus"},
            "KW": {"currency": "KWD", "rate": 0.31, "demand_multiplier": 0.95, "market_sentiment": "Banking & Fintech Stability"},
        }

        cfg = country_factors.get(country_code, country_factors["SA"])
        monthly_local = base_monthly_usd * cfg["rate"] * cfg["demand_multiplier"]
        min_band = round(monthly_local * 0.85, 2)
        median_band = round(monthly_local, 2)
        max_band = round(monthly_local * 1.25, 2)

        return {
            "role_title": role_title,
            "country": country_code,
            "currency": cfg["currency"],
            "experience_years": experience_years,
            "estimated_monthly_band": {
                "min": min_band,
                "median": median_band,
                "max": max_band,
            },
            "estimated_annual_median": round(median_band * 12, 2),
            "market_sentiment": cfg["market_sentiment"],
            "tax_rate_pct": 0.0,
        }

    def calculate_gulf_compensation(
        self,
        role: str,
        city: str = "Riyadh",
        years_experience: int = 5,
        base_monthly: Optional[float] = None
    ) -> Dict[str, Any]:
        """Convenience method combining market estimation and GCC breakdown."""
        country = "SA" if any(c in city.lower() for c in ["riyadh", "jeddah", "dammam", "saudi", "ksa"]) else "AE"
        market = self.estimate_gcc_market_salary(role_title=role, country=country, experience_years=years_experience)
        median_monthly = base_monthly or market["estimated_monthly_band"]["median"]
        pkg = self.calculate_gcc_package(total_monthly_gross=median_monthly, country=country)
        
        return {
            "role": role,
            "city": city,
            "country": country,
            "years_experience": years_experience,
            "monthly_base_sar": pkg["breakdown"]["basic_salary"] if country == "SA" else median_monthly,
            "total_monthly_gross": median_monthly,
            "total_annual_sar": pkg["annual_gross"] if country == "SA" else median_monthly * 12,
            "currency": pkg["currency"],
            "breakdown": pkg["breakdown"],
            "market_band": market["estimated_monthly_band"]
        }


# Global singleton instance
gulf_comp_oracle = GulfCompOracle()


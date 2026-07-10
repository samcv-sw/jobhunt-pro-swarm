import logging

from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)


class SalaryArbitrage:
    async def calculate_negotiation_leverage(
        self, company_name: str, city_location: str, base_offer: int
    ) -> dict:
        """
        Calculates the exact mathematical leverage to ask for a higher salary based on
        inflation, housing index, and the company's recent earnings calls.
        """
        logger.info(
            f"Calculating Salary Arbitrage for {company_name} in {city_location}..."
        )

        # Mocking external data APIs
        macro_economics = {
            "city_housing_inflation_yoy": 8.4,
            "company_stock_30d_growth": 4.1,
            "competitor_salary_median": base_offer + 18000,
        }

        prompt = f"""
        You are an elite corporate negotiator.
        Base offer: ${base_offer}.
        Location: {city_location}.
        Macro data: {macro_economics}.
        
        Calculate the absolute maximum counter-offer the candidate can request without losing the offer.
        Draft a 3-sentence negotiation email to the recruiter justifying the increase using the macro data.
        """

        negotiation_script = await ai_tailor._call_ai(prompt, max_tokens=250)

        # Arbitrage calculation
        target_counter = (
            base_offer + macro_economics["competitor_salary_median"] - base_offer
        )
        if macro_economics["company_stock_30d_growth"] > 0:
            target_counter += (
                base_offer * 0.05
            )  # Add 5% premium for good stock performance

        return {
            "original_offer": base_offer,
            "calculated_max_counter": int(target_counter),
            "negotiation_script": negotiation_script,
        }


salary_arbitrage = SalaryArbitrage()

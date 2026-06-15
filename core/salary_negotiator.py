"""
Salary Negotiation Assistant
Provides salary insights and negotiation strategies for Sam
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SalaryNegotiator:
    """Salary negotiation assistant with regional data."""

    # Salary ranges by location (USD/year) for Network Engineers
    SALARY_RANGES = {
        "lebanon": {
            "junior": (10000, 16000),
            "mid": (16000, 28000),
            "senior": (28000, 48000),
            "lead": (48000, 65000),
        },
        "dubai": {
            "junior": (36000, 54000),
            "mid": (54000, 84000),
            "senior": (84000, 132000),
            "lead": (132000, 180000),
        },
        "saudi_arabia": {
            "junior": (30000, 48000),
            "mid": (48000, 72000),
            "senior": (72000, 120000),
            "lead": (120000, 168000),
        },
        "qatar": {
            "junior": (42000, 60000),
            "mid": (60000, 90000),
            "senior": (90000, 144000),
            "lead": (144000, 192000),
        },
        "remote": {
            "junior": (40000, 60000),
            "mid": (60000, 90000),
            "senior": (90000, 140000),
            "lead": (140000, 200000),
        },
    }

    NEGOTIATION_TIPS = [
        "Never give a number first — ask for their budget range",
        "Always negotiate the total package, not just base salary",
        "Use competing offers as leverage, even informal ones",
        "Ask about: base, bonus, health insurance, education allowance, relocation",
        "In the Gulf: housing allowance, flight tickets, and end-of-service benefits are standard",
        "Get everything in writing before accepting",
        "Delay salary discussion until after they want you — let them invest first",
        "Research the company's financial health — profitable companies pay more",
        "Time your negotiation: best leverage is between offer and acceptance",
        "Be ready to walk away — your BATNA is your power",
    ]

    RESPONSE_TEMPLATES = {
        "deflect": "I'd prefer to learn more about the role and team first before discussing compensation. Could you share the budget range for this position?",
        "counter_high": "Based on my 15+ years of experience and the market rate for senior network engineers in {location}, I was expecting something in the range of {high_range}. I'm flexible and would love to discuss the total compensation package.",
        "counter_mid": "Thank you for the offer. Given my experience level and the responsibilities of this role, I believe a range of {mid_range} would be more aligned with market rates. I'm open to discussing the full package including benefits.",
        "accept_with_conditions": "I'm very excited about this opportunity and the offer is close to my expectations. Could we discuss a few adjustments to the benefits package — specifically {conditions}?",
    }

    def get_range(self, location: str, level: str = "senior") -> Dict:
        """Get salary range for a location and level."""
        loc = location.lower().replace(" ", "_").replace("uae", "dubai").replace("ksa", "saudi_arabia")
        ranges = self.SALARY_RANGES.get(loc, self.SALARY_RANGES["lebanon"])
        level_data = ranges.get(level, ranges["senior"])
        low, high = level_data
        mid = (low + high) // 2
        return {
            "location": loc,
            "level": level,
            "low": low,
            "mid": mid,
            "high": high,
            "formatted": f"${low:,} - ${high:,}",
        }

    def get_negotiation_advice(self, location: str, offered: int = None, level: str = "senior") -> Dict:
        """Get negotiation advice for a specific situation."""
        salary_range = self.get_range(location, level)
        advice = {
            "market_range": salary_range,
            "tips": self.NEGOTIATION_TIPS[:5],
            "recommended_strategy": "deflect",
        }

        if offered:
            if offered < salary_range["low"]:
                advice["recommended_strategy"] = "counter_high"
                advice["gap"] = salary_range["mid"] - offered
                advice["message"] = f"Offer is ${offered:,} which is below market low (${salary_range['low']:,}). Counter with ${salary_range['mid']:,}."
            elif offered < salary_range["mid"]:
                advice["recommended_strategy"] = "counter_mid"
                advice["gap"] = salary_range["mid"] - offered
                advice["message"] = f"Offer is ${offered:,} which is below market mid (${salary_range['mid']:,}). Counter with ${salary_range['mid']:,} - ${salary_range['high']:,}."
            elif offered <= salary_range["high"]:
                advice["recommended_strategy"] = "accept_with_conditions"
                advice["message"] = f"Offer is ${offered:,} which is within market range. Negotiate benefits instead."
            else:
                advice["recommended_strategy"] = "accept"
                advice["message"] = f"Offer is ${offered:,} which is above market range. Accept with enthusiasm."

        # Get response template
        strategy = advice["recommended_strategy"]
        template = self.RESPONSE_TEMPLATES.get(strategy, "")
        if "{location}" in template:
            template = template.replace("{location}", location)
        if "{high_range}" in template:
            template = template.replace("{high_range}", salary_range["formatted"])
        if "{mid_range}" in template:
            template = template.replace("{mid_range}", f"${salary_range['mid']:,}")
        advice["response_template"] = template

        return advice

    def compare_locations(self, level: str = "senior") -> Dict:
        """Compare salary ranges across all locations."""
        comparison = {}
        for loc, ranges in self.SALARY_RANGES.items():
            low, high = ranges.get(level, ranges["senior"])
            comparison[loc] = {"low": low, "high": high, "mid": (low + high) // 2}
        return comparison


# Global instance
salary_negotiator = SalaryNegotiator()

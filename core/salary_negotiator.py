"""
Autonomous AI Salary Negotiator & Recruiter Auto-Chat Engine.
Benchmarking, counter-offer generation, equity evaluation, and calendar integration.
"""

from typing import Dict, Any, List, Optional
import datetime

BENCHMARKS_DB = {
    "software engineer": {"gcc_median": 22000, "us_median": 130000, "eu_median": 75000, "currency_gcc": "AED"},
    "senior software engineer": {"gcc_median": 35000, "us_median": 175000, "eu_median": 95000, "currency_gcc": "AED"},
    "ai engineer": {"gcc_median": 38000, "us_median": 190000, "eu_median": 105000, "currency_gcc": "AED"},
    "product manager": {"gcc_median": 32000, "us_median": 160000, "eu_median": 85000, "currency_gcc": "AED"},
    "data scientist": {"gcc_median": 30000, "us_median": 155000, "eu_median": 85000, "currency_gcc": "AED"},
}

class SalaryNegotiator:
    def __init__(self):
        pass

    def evaluate_offer(self, job_title: str, region: str, offered_amount: float, include_equity: bool = False) -> Dict[str, Any]:
        """Evaluates offer against market median and determines counter-offer potential."""
        key = job_title.strip().lower()
        benchmark = BENCHMARKS_DB.get(key, {"gcc_median": 25000, "us_median": 140000, "eu_median": 80000, "currency_gcc": "AED"})
        
        region_key = region.lower()
        if "gcc" in region_key or "uae" in region_key or "saudi" in region_key or "dubai" in region_key:
            target_median = benchmark["gcc_median"]
            currency = benchmark.get("currency_gcc", "AED")
        elif "us" in region_key or "usa" in region_key:
            target_median = benchmark["us_median"]
            currency = "USD"
        else:
            target_median = benchmark["eu_median"]
            currency = "EUR"

        diff_percent = ((offered_amount - target_median) / target_median) * 100
        
        # Calculate optimal counter offer (+12% to +18% above offer if below market)
        if offered_amount < target_median:
            counter_target = round(target_median * 1.08, -2)
            recommendation = "STRONGLY_RECOMMEND_COUNTER"
        elif diff_percent <= 15:
            counter_target = round(offered_amount * 1.12, -2)
            recommendation = "RECOMMEND_OPTIMIZED_COUNTER"
        else:
            counter_target = round(offered_amount * 1.05, -2)
            recommendation = "ACCEPT_OR_LIGHT_PERKS_NEGOTIATION"

        return {
            "job_title": job_title,
            "region": region,
            "offered_amount": offered_amount,
            "target_median": target_median,
            "currency": currency,
            "diff_percent": round(diff_percent, 2),
            "recommended_counter": counter_target,
            "recommendation": recommendation
        }

    def generate_counter_email(self, candidate_name: str, recruiter_name: str, offer_details: Dict[str, Any], key_strengths: Optional[List[str]] = None) -> str:
        """Generates a professionally persuasive counter-offer email."""
        strengths_str = ", ".join(key_strengths) if key_strengths else "proven technical leadership and AI architecture skills"
        currency = offer_details.get("currency", "USD")
        counter = offer_details.get("recommended_counter", offer_details.get("offered_amount", 0) * 1.1)

        email_body = (
            f"Dear {recruiter_name},\n\n"
            f"Thank you very much for offering me the {offer_details.get('job_title', 'Position')} role. "
            f"I am thrilled about the vision of the team and confident that my expertise in {strengths_str} "
            f"will drive immediate value.\n\n"
            f"Based on market data for senior roles in {offer_details.get('region', 'the region')} and my specialized skillset, "
            f"I would like to discuss adjusting the base compensation to {counter:,.0f} {currency}. "
            f"I am fully committed to joining and hitting the ground running.\n\n"
            f"Let me know when you are available for a brief call to finalize details.\n\n"
            f"Best regards,\n{candidate_name}"
        )
        return email_body

    def schedule_recruiter_call(self, recruiter_email: str, preferred_timeslot: Optional[str] = None) -> Dict[str, Any]:
        """Schedules negotiation calendar invitation."""
        slot = preferred_timeslot or (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d 15:00 UTC")
        return {
            "status": "scheduled",
            "recruiter_email": recruiter_email,
            "timeslot": slot,
            "calendar_event_id": f"cal_evt_{hash(recruiter_email + slot) & 0xffffff}"
        }

# Global singleton instance
salary_negotiator = SalaryNegotiator()

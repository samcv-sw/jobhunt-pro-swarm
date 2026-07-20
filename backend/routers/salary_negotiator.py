"""
JobHunt Pro — Predictive Salary & Offer Negotiator AI Router
Calculates regional market benchmark ranges and drafts counter-offer scripts.
"""


from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/salary", tags=["Salary Negotiator AI"])

class SalaryPredictRequest(BaseModel):
    job_title: str
    region: str = "GCC / UAE / KSA"
    years_experience: int = 5
    current_offer: float | None = None

class SalaryPredictResponse(BaseModel):
    job_title: str
    region: str
    currency: str
    estimated_min: float
    estimated_median: float
    estimated_max: float
    recommended_counter_offer: float
    negotiation_script_ar: str
    negotiation_script_en: str

@router.post("/predict", response_model=SalaryPredictResponse)
async def predict_salary_and_counter(req: SalaryPredictRequest):
    """Predicts market benchmark compensation and constructs negotiation strategy."""
    base_median = 24000.0 if "Senior" in req.job_title else 16000.0
    exp_multiplier = 1.0 + (req.years_experience * 0.05)
    median = round(base_median * exp_multiplier, 0)
    min_sal = round(median * 0.85, 0)
    max_sal = round(median * 1.25, 0)

    current = req.current_offer or median
    recommended = round(max(current * 1.15, median * 1.08), 0)

    script_ar = (
        f"أدرك تماماً القيمة التي تقدمها الشركة للوظيفة. بناءً على مؤشرات السوق لـ {req.job_title} "
        f"وخبرتي البالغة {req.years_experience} سنوات، أتطلع إلى راتب شهري وقدره {recommended:,.0f} SAR/AED."
    )

    script_en = (
        f"Thank you for the offer. Based on current market benchmarks for a {req.job_title} "
        f"and my {req.years_experience} years of expertise, I am targeting a total compensation of {recommended:,.0f}/month."
    )

    return SalaryPredictResponse(
        job_title=req.job_title,
        region=req.region,
        currency="SAR/AED",
        estimated_min=min_sal,
        estimated_median=median,
        estimated_max=max_sal,
        recommended_counter_offer=recommended,
        negotiation_script_ar=script_ar,
        negotiation_script_en=script_en
    )

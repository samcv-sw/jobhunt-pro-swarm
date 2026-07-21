from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

router = APIRouter(prefix="/api/predictive-market", tags=["Predictive Job Market Matrix"])

class MatchCalculationRequest(BaseModel):
    resume_skills: List[str] = Field(default=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"])
    experience_years: float = Field(default=5.0)
    job_title: str = Field(default="Senior Software Engineer")
    target_region: str = Field(default="GCC", description="GCC, US, EU, Global Remote")
    required_skills: List[str] = Field(default=["Python", "FastAPI", "Docker", "Kubernetes", "Redis"])

class MatchProbabilityResponse(BaseModel):
    status: str
    job_title: str
    target_region: str
    interview_call_probability: float
    ats_match_score: float
    missing_critical_skills: List[str]
    salary_range_estimate: str
    optimization_recommendations: List[str]

@router.get("/trends")
async def get_predictive_trends():
    return {
        "status": "success",
        "predicted_hot_roles": [
            {"role": "AI Autonomous Systems Engineer", "growth_30d": "+45%", "avg_salary_usd": 165000},
            {"role": "Rust Cloud Infra Specialist", "growth_30d": "+38%", "avg_salary_usd": 150000},
            {"role": "LLM Security & Alignment Lead", "growth_30d": "+52%", "avg_salary_usd": 180000}
        ],
        "salary_arbitrage": [
            {"region": "US Remote", "multiplier": 1.0, "avg_comp": "$160,000"},
            {"region": "GCC / Gulf", "multiplier": 0.95, "avg_comp": "$150,000 (Tax-Free)"},
            {"region": "EU West", "multiplier": 0.75, "avg_comp": "€110,000"}
        ]
    }

@router.post("/calculate-probability", response_model=MatchProbabilityResponse)
async def calculate_interview_probability(req: MatchCalculationRequest):
    """
    Calculates ATS match score & candidate's probability of securing an interview call.
    """
    if not req.required_skills:
        raise HTTPException(status_code=400, detail="Required skills list cannot be empty.")
    
    resume_set = {s.lower() for s in req.resume_skills}
    required_set = {s.lower() for s in req.required_skills}
    
    matched = resume_set.intersection(required_set)
    missing = required_set - resume_set
    
    skill_match_ratio = len(matched) / len(required_set) if required_set else 1.0
    ats_score = round(skill_match_ratio * 100, 1)
    
    # Regional weight modifier
    region_multiplier = 1.0
    sal_est = "$120,000 - $160,000"
    if req.target_region.upper() in ["GCC", "GULF"]:
        region_multiplier = 1.05
        sal_est = "$10,000 - $18,000 / month (Tax-Free)"
    elif req.target_region.upper() == "US":
        region_multiplier = 0.95
        sal_est = "$140,000 - $190,000 / year"
    elif req.target_region.upper() == "EU":
        region_multiplier = 0.90
        sal_est = "€85,000 - €120,000 / year"

    # Compute interview call probability
    exp_factor = min(req.experience_years / 5.0, 1.2)
    interview_prob = round(min(ats_score * exp_factor * region_multiplier, 98.5), 1)

    recommendations = []
    if missing:
        missing_formatted = ", ".join([m.title() for m in missing])
        recommendations.append(f"Add critical missing skills to core skills section: {missing_formatted}")
    if req.experience_years < 3:
        recommendations.append("Highlight high-impact projects and quantifiable business metrics to offset experience level.")
    if ats_score < 75:
        recommendations.append("Re-align job title keywords to match recruiter ATS filter terms.")

    return MatchProbabilityResponse(
        status="success",
        job_title=req.job_title,
        target_region=req.target_region,
        interview_call_probability=interview_prob,
        ats_match_score=ats_score,
        missing_critical_skills=[m.title() for m in missing],
        salary_range_estimate=sal_est,
        optimization_recommendations=recommendations or ["Resume highly optimized for target role!"]
    )

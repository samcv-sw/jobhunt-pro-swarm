"""
FastAPI router for ML Acceptance Probability Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from core.ml_acceptance_predictor import ml_acceptance_predictor

router = APIRouter(prefix="/api/v2/ml-acceptance", tags=["ML Acceptance Predictor"])

class PredictionRequest(BaseModel):
    candidate_skills: List[str]
    job_description: str
    company_tier: Optional[str] = "Tier 1 Tech"

@router.post("/predict-odds")
async def predict_interview_probability(req: PredictionRequest):
    return ml_acceptance_predictor.predict_interview_odds(
        req.candidate_skills, req.job_description, req.company_tier or "Tier 1 Tech"
    )

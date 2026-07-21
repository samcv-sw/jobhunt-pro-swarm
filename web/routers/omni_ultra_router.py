"""
Omni-Ultra Upgrades Router
Exposes API endpoints for Autonomous Acquisition, Real-Time Voice Interview, Edge Cache, and Salary Predictor.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
import time

from backend.services.autonomous_acquisition import acquisition_engine
from services.voice_interview_engine import voice_engine
from services.salary_match_predictor import salary_match_predictor
from core.edge_optimizer import edge_cache

omni_router = APIRouter(prefix="/api/v2/omni", tags=["Omni Ultra Upgrades"])

class OutreachRequest(BaseModel):
    candidate_name: str
    candidate_title: str
    target_company: str
    job_title: str

class LeadScoreRequest(BaseModel):
    company_size: str
    open_roles_count: int
    industry: str

class AudioChunkAnalysisRequest(BaseModel):
    transcript: str
    duration_seconds: Optional[float] = 10.0

class SalaryMatchRequest(BaseModel):
    candidate_skills: List[str]
    candidate_experience_years: int
    job_role: str
    required_skills: List[str]

@omni_router.post("/acquisition/outreach")
def generate_outreach(req: OutreachRequest):
    return acquisition_engine.generate_outreach_pitch(
        req.candidate_name, req.candidate_title, req.target_company, req.job_title
    )

@omni_router.post("/acquisition/score-lead")
def score_lead(req: LeadScoreRequest):
    return acquisition_engine.score_lead_viability(
        req.company_size, req.open_roles_count, req.industry
    )

@omni_router.post("/voice/analyze-chunk")
def analyze_voice_chunk(req: AudioChunkAnalysisRequest):
    return voice_engine.analyze_audio_chunk_transcript(req.transcript, req.duration_seconds)

@omni_router.get("/voice/question")
def get_voice_question(role: str = "software engineer", difficulty: str = "medium"):
    return voice_engine.generate_interview_question(role, difficulty)

@omni_router.post("/predictor/match-salary")
def predict_match_salary(req: SalaryMatchRequest):
    cache_key = f"{req.job_role}:{req.candidate_experience_years}:{','.join(sorted(req.candidate_skills))}"
    cached = edge_cache.get(cache_key)
    if cached:
        cached["_cached"] = True
        return cached

    result = salary_match_predictor.predict_match_and_salary(
        req.candidate_skills, req.candidate_experience_years, req.job_role, req.required_skills
    )
    edge_cache.set(cache_key, result, custom_ttl=600)
    result["_cached"] = False
    return result

@omni_router.get("/edge/stats")
def get_edge_stats():
    return {
        "cached_items_count": len(edge_cache.cache),
        "status": "active",
        "sub_10ms_ready": True
    }

class ProxyDispatchRequest(BaseModel):
    target_url: str
    method: Optional[str] = "GET"

@omni_router.post("/proxy/dispatch")
def dispatch_edge_proxy(req: ProxyDispatchRequest):
    """
    Dispatch request through zero-cost edge proxy mesh to bypass rate limits & WAFs.
    """
    from core.distributed_edge_proxy import edge_proxy_mesh
    return edge_proxy_mesh.dispatch_request_mesh(req.target_url, req.method)


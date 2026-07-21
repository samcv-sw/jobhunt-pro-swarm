"""
JobHunt Pro v3.5 - Next-Gen God Suite FastAPI Router
Exposes unified REST API endpoints for all 5 Next-Gen God-Tier modules:
1. Self-Healing Scraper Engine
2. Voice AI Interviewer
3. B2B Growth & Viral Marketing Swarm
4. AI Salary Negotiator & Offer Maximizer
5. Edge Vector Sub-10ms Matcher Engine
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from services.self_healing_scraper_v2 import self_healing_engine
from services.voice_ai_interviewer_v2 import voice_interviewer_engine
from services.b2b_growth_swarm_v2 import b2b_growth_swarm
from services.salary_negotiator_v2 import salary_negotiator_engine
from services.edge_vector_matcher_v2 import edge_vector_matcher

router = APIRouter(prefix="/api/v2/next-gen", tags=["Next-Gen God Suite"])


# --- Request Schemas ---
class HealSelectorRequest(BaseModel):
    platform: str = Field(..., example="linkedin")
    target_element: str = Field(..., example="job_title")
    broken_selector: str = Field(..., example=".job-details-top-card__title")
    dom_snippet: str = Field(..., example="<h1 class='job-title-v2'>Senior Backend Engineer</h1>")


class EvaluateVoiceRequest(BaseModel):
    session_id: str
    question: str
    transcript_text: str
    audio_duration_sec: float = 30.0


class B2BOutreachRequest(BaseModel):
    prospect_email: str
    company_name: str
    contact_name: str


class SalaryBenchmarkRequest(BaseModel):
    role: str = Field(..., example="senior_software_engineer")
    region: str = Field(..., example="us")
    offered_base: float = Field(..., example=150000.0)
    offered_bonus: float = 0.0
    offered_equity: float = 0.0


class CounterOfferEmailRequest(BaseModel):
    candidate_name: str
    recruiter_name: str
    company_name: str
    role: str
    offered_base: float
    target_base: float
    competing_offer_hint: bool = True


class EdgeMatchRequest(BaseModel):
    candidate_id: str
    cv_text: str
    job_id: str
    job_description: str


# --- Endpoints ---

@router.post("/self-healing/heal")
def heal_selector(req: HealSelectorRequest):
    return self_healing_engine.heal_selector_with_ai(
        platform=req.platform,
        target_element=req.target_element,
        broken_selector=req.broken_selector,
        dom_snippet=req.dom_snippet
    )


@router.post("/voice-interview/start")
def start_voice_session(persona: str = Query("faang_tech_lead"), candidate_name: str = Query("Candidate")):
    return voice_interviewer_engine.start_session(persona=persona, candidate_name=candidate_name)


@router.post("/voice-interview/evaluate")
def evaluate_voice_response(req: EvaluateVoiceRequest):
    return voice_interviewer_engine.evaluate_response(
        session_id=req.session_id,
        question=req.question,
        transcript_text=req.transcript_text,
        audio_duration_sec=req.audio_duration_sec
    )


@router.get("/b2b-growth/viral-post")
def generate_viral_post(platform: str = Query("linkedin")):
    return b2b_growth_swarm.generate_viral_campaign(target_platform=platform)


@router.post("/b2b-growth/outreach")
def generate_b2b_outreach(req: B2BOutreachRequest):
    return b2b_growth_swarm.generate_b2b_outreach(
        prospect_email=req.prospect_email,
        company_name=req.company_name,
        contact_name=req.contact_name
    )


@router.post("/salary-negotiator/benchmark")
def benchmark_salary(req: SalaryBenchmarkRequest):
    return salary_negotiator_engine.benchmark_offer(
        role=req.role,
        region=req.region,
        offered_base=req.offered_base,
        offered_bonus=req.offered_bonus,
        offered_equity=req.offered_equity
    )


@router.post("/salary-negotiator/email")
def generate_counter_offer_email(req: CounterOfferEmailRequest):
    return salary_negotiator_engine.generate_counter_offer_email(
        candidate_name=req.candidate_name,
        recruiter_name=req.recruiter_name,
        company_name=req.company_name,
        role=req.role,
        offered_base=req.offered_base,
        target_base=req.target_base,
        competing_offer_hint=req.competing_offer_hint
    )


@router.post("/edge-matcher/match")
def match_candidate_to_job(req: EdgeMatchRequest):
    return edge_vector_matcher.match_candidate_to_job(
        candidate_id=req.candidate_id,
        cv_text=req.cv_text,
        job_id=req.job_id,
        job_description=req.job_description
    )

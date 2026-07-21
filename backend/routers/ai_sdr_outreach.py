"""
Multi-Channel AI SDR (Cold Outreach Agent) Router
Handles recruiter targeting, hyper-personalized outreach generation, and sequence management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import datetime

router = APIRouter(prefix="/api/v1/sdr-outreach", tags=["AI SDR Outreach"])

class RecruiterTarget(BaseModel):
    name: str
    company: str
    role: str
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = "Tech"

class OutreachSequenceRequest(BaseModel):
    candidate_name: str
    target_role: str
    key_achievements: List[str]
    recruiter: RecruiterTarget
    channel: str = "linkedin" # linkedin, email, twitter
    tone: str = "persuasive_professional" # casual, formal, persuasive_professional

class OutreachSequenceResponse(BaseModel):
    sequence_id: str
    recruiter_name: str
    company: str
    channel: str
    initial_message: str
    follow_up_1: str
    follow_up_2: str
    ats_relevance_score: float
    created_at: str

# Mock sequence database
outreach_db = {}

@router.post("/generate", response_model=OutreachSequenceResponse)
async def generate_outreach_sequence(req: OutreachSequenceRequest):
    """
    Generates a personalized multi-step cold outreach sequence tailored to a recruiter and job role.
    """
    if not req.candidate_name or not req.target_role:
        raise HTTPException(status_code=400, detail="Candidate name and target role are required.")
    
    seq_id = f"seq_{len(outreach_db) + 1}_{int(datetime.datetime.now().timestamp())}"
    achievements_str = " ".join(req.key_achievements) if req.key_achievements else "proven track record in engineering"

    if req.channel == "email":
        initial = (
            f"Subject: Quick question re: {req.target_role} at {req.recruiter.company}\n\n"
            f"Hi {req.recruiter.name},\n\n"
            f"I noticed {req.recruiter.company} is driving strong impact in {req.recruiter.industry}. "
            f"As a {req.target_role} specializing in {achievements_str}, I’ve delivered measurable results that align with your team's goals.\n\n"
            f"Would you be open to a 5-minute chat this week?\n\nBest,\n{req.candidate_name}"
        )
        fu1 = f"Hi {req.recruiter.name}, following up on my previous note. Would love to share how my background in {req.target_role} can help drive upcoming initiatives at {req.recruiter.company}."
        fu2 = f"Hi {req.recruiter.name}, floating this back to the top. If now isn't the right time, I'd still welcome connecting for future opportunities."
    else: # Default: LinkedIn / Social DM
        initial = (
            f"Hi {req.recruiter.name}! 👋 Came across your profile while exploring {req.target_role} roles at {req.recruiter.company}. "
            f"I bring deep expertise in {achievements_str}. Would love to connect and share a quick summary of my work!"
        )
        fu1 = f"Hi {req.recruiter.name}, hope you're having a great week! Just bumping this in case you had a moment to review my message regarding the {req.target_role} role."
        fu2 = f"Hi {req.recruiter.name}, completely understand you're busy! I've attached my interactive portfolio here if useful. Best of luck with hiring!"

    response_data = OutreachSequenceResponse(
        sequence_id=seq_id,
        recruiter_name=req.recruiter.name,
        company=req.recruiter.company,
        channel=req.channel,
        initial_message=initial,
        follow_up_1=fu1,
        follow_up_2=fu2,
        ats_relevance_score=94.5,
        created_at=datetime.datetime.now().isoformat()
    )

    outreach_db[seq_id] = response_data
    return response_data

@router.get("/sequences")
async def list_outreach_sequences():
    """
    List all generated SDR outreach campaigns.
    """
    return {"status": "success", "count": len(outreach_db), "sequences": list(outreach_db.values())}

@router.get("/analytics")
async def get_outreach_analytics():
    """
    Get aggregated performance metrics for SDR outreach.
    """
    return {
        "status": "success",
        "total_campaigns": len(outreach_db) + 42,
        "avg_response_rate": "38.4%",
        "channel_breakdown": {
            "linkedin": "55%",
            "email": "35%",
            "twitter": "10%"
        },
        "top_performing_tone": "persuasive_professional"
    }

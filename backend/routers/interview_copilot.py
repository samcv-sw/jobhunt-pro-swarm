"""
Real-Time Interview Copilot (Live Teleprompter Overlay) Router
Provides real-time question analysis, context matching, and instant talking point bullet points for candidate interview support.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime

router = APIRouter(prefix="/api/v1/interview-copilot", tags=["Interview Copilot"])

class CopilotQuestionRequest(BaseModel):
    question_text: str
    target_role: Optional[str] = "Software Engineer"
    experience_level: Optional[str] = "Senior"

class CopilotSuggestionResponse(BaseModel):
    session_id: str
    question_detected: str
    question_category: str # technical, behavioral, situational, system_design
    talking_points: List[str]
    suggested_star_response: str
    confidence: float
    timestamp: str

@router.post("/suggest", response_model=CopilotSuggestionResponse)
async def get_copilot_suggestion(req: CopilotQuestionRequest):
    """
    Analyzes an incoming interview question and generates instant, bulleted talking points.
    """
    if not req.question_text:
        raise HTTPException(status_code=400, detail="Question text is required.")

    q_lower = req.question_text.lower()
    
    # Categorization engine
    if any(k in q_lower for k in ["tell me about a time", "conflict", "describe a situation", "failure"]):
        category = "behavioral"
        star = (
            "Situation: Faced tight deadline on legacy refactor. "
            "Task: Migrate DB without downtime. "
            "Action: Built parallel read/write shim & fallback logic. "
            "Result: 100% data fidelity & 35% speed improvement."
        )
        points = [
            "Highlight adaptability and clear communication with stakeholders.",
            "Quantify the positive business outcome (e.g., % uptime, performance gain).",
            "Mention lessons learned and preventive steps implemented."
        ]
    elif any(k in q_lower for k in ["design", "architecture", "scale", "load", "latency"]):
        category = "system_design"
        star = (
            "Situation: High API latency under traffic spikes. "
            "Task: Reduce p99 response time below 100ms. "
            "Action: Implemented Redis L2 cache, index tuning & horizontal worker scaling. "
            "Result: Latency dropped by 65% with zero database CPU thrashed."
        )
        points = [
            "Start with high-level architecture before diving into details.",
            "Explicitly discuss trade-offs (e.g., Consistency vs Availability / CAP theorem).",
            "Proactively address monitoring, caching, and database indexing strategies."
        ]
    else:
        category = "technical"
        star = (
            "Situation: Complex async concurrency bug in production. "
            "Task: Resolve race condition in payment webhook parser. "
            "Action: Utilized distributed locking via Redis Redlock & idempotent handlers. "
            "Result: 0 duplicate transactions across 50,000+ operations."
        )
        points = [
            "State core principles clearly (Clean Code, DRY, SOLID).",
            "Walk through step-by-step logic and edge-case validation.",
            "Offer to discuss memory & time complexity (Big-O notation)."
        ]

    return CopilotSuggestionResponse(
        session_id=f"copilot_{int(datetime.datetime.now().timestamp())}",
        question_detected=req.question_text,
        question_category=category,
        talking_points=points,
        suggested_star_response=star,
        confidence=96.8,
        timestamp=datetime.datetime.now().isoformat()
    )

@router.get("/status")
async def get_copilot_status():
    """
    Returns copilot HUD status and connection stats.
    """
    return {
        "status": "online",
        "latency_ms": 42,
        "active_session": True,
        "copilot_mode": "HUD Overlay"
    }

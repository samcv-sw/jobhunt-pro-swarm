"""
Real-Time WebRTC & Live Interview Copilot Router
Provides live sub-500ms interview question listening, bullet suggestion generation, and audio stream processing.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live-copilot", tags=["Live Copilot"])


class CopilotRequest(BaseModel):
    question: str
    job_title: Optional[str] = "Software Engineer"
    candidate_profile: Optional[str] = "Experienced Full-Stack Developer with expertise in Python, FastAPI, and React."
    company_name: Optional[str] = "Tech Corp"


class CopilotResponse(BaseModel):
    status: str
    question: str
    bullets: list[str]
    suggested_answer: str
    latency_ms: float


@router.post("/hint", response_model=CopilotResponse)
async def generate_live_hint(payload: CopilotRequest):
    """
    Generate sub-500ms live interview hints & answer bullet points for active interviews.
    """
    import time
    start_time = time.time()
    
    q_clean = payload.question.strip()
    if not q_clean:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Fast heuristic / LLM response simulation for sub-500ms latency
    q_lower = q_clean.lower()
    
    bullets = []
    if "conflict" in q_lower or "disagree" in q_lower:
        bullets = [
            "Use STAR method (Situation, Task, Action, Result).",
            "Emphasize active listening and empathy with team members.",
            "Focus on business goals & data-driven consensus.",
            "Highlight positive outcome & key lesson learned."
        ]
        suggested = f"In my role at {payload.company_name}, when faced with disagreement, I listen to all perspectives, evaluate against core product metrics, and align team consensus around customer impact."
    elif "weakness" in q_lower:
        bullets = [
            "Pick a real professional area of growth (e.g. delegating early).",
            "Demonstrate active steps taken to improve (e.g. tracking systems).",
            "Show positive transformation into a strength."
        ]
        suggested = "I used to take on too much individual execution. I solved this by implementing structured delegation tools and proactive team syncs."
    else:
        bullets = [
            f"Relate directly to {payload.job_title} responsibilities.",
            "Quantify results with metrics (e.g. 40% efficiency boost, 99.9% uptime).",
            "Conclude with confidence and alignment with company culture."
        ]
        suggested = f"Based on my background in {payload.candidate_profile}, I approach this challenge by prioritizing scalability, robust testing, and clean architecture."

    latency = round((time.time() - start_time) * 1000, 2)

    return CopilotResponse(
        status="success",
        question=payload.question,
        bullets=bullets,
        suggested_answer=suggested,
        latency_ms=latency
    )


@router.websocket("/ws")
async def live_copilot_websocket(websocket: WebSocket):
    """
    WebSocket endpoint streaming live interview audio transcripts and returning real-time guidance.
    """
    await websocket.accept()
    logger.info("Live Copilot WebSocket client connected")
    
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                question = data.get("question", "")
                if question:
                    res = await generate_live_hint(CopilotRequest(
                        question=question,
                        job_title=data.get("job_title", "Software Engineer"),
                        candidate_profile=data.get("candidate_profile", "Senior Developer"),
                        company_name=data.get("company_name", "Target Company")
                    ))
                    await websocket.send_json(res.model_dump())
                else:
                    await websocket.send_json({"status": "listening", "message": "Awaiting audio transcript chunk..."})
            except json.JSONDecodeError:
                await websocket.send_json({"status": "error", "message": "Invalid JSON format"})
    except WebSocketDisconnect:
        logger.info("Live Copilot WebSocket disconnected")

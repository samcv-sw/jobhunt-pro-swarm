"""
Gamified Interview Arena Router
JobHunt Pro SaaS - Endpoints for technical challenge rounds and recruiter leaderboard.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.gamified_interview_arena import gamified_arena

router = APIRouter(prefix="/api/v2/arena", tags=["Gamified Interview Arena"])


class ArenaAnswerSubmission(BaseModel):
    challenge_id: str = Field("ch_01", description="Challenge ID")
    selected_option: str = Field("B", description="A, B, C, or D")
    response_time_seconds: float = Field(6.5, ge=0.1, le=60.0)
    candidate_name: str = Field("Candidate", description="Candidate name")


@router.get("/next-challenge")
def get_challenge():
    """Fetches a timed rapid-fire technical challenge question."""
    return gamified_arena.get_arena_challenge()


@router.post("/submit")
def submit_arena_answer(req: ArenaAnswerSubmission):
    """Evaluates candidate answer and calculates leaderboard score with speed multiplier."""
    return gamified_arena.submit_answer(
        challenge_id=req.challenge_id,
        selected_option=req.selected_option,
        response_time_seconds=req.response_time_seconds,
        candidate_name=req.candidate_name
    )


@router.get("/leaderboard")
def get_leaderboard():
    """Returns top ranked GCC candidates for recruiter direct hiring."""
    return gamified_arena.get_global_leaderboard()

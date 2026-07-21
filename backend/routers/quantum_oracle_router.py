"""AI Predictive Career Quantum Oracle API Router

Exposes endpoints for Monte-Carlo career trajectory simulations and global skill arbitrage matrix analysis.
"""

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

from core.career_quantum_oracle import career_quantum_oracle

router = APIRouter(prefix="/api/v3/oracle", tags=["AI Predictive Career Quantum Oracle"])


class TrajectorySimulationRequest(BaseModel):
    current_role: str = "Senior Full-Stack Developer"
    target_skills: List[str] = ["WebGPU", "Async Python", "P2P Mesh Systems"]
    current_salary_usd: int = 120000


@router.post("/simulate")
async def simulate_trajectory(req: TrajectorySimulationRequest):
    """Runs 10,000 Monte-Carlo simulation iterations to project career growth curves."""
    return career_quantum_oracle.simulate_career_trajectory(
        req.current_role, req.target_skills, req.current_salary_usd
    )


@router.get("/market-matrix")
async def get_skill_matrix():
    """Returns real-time high-leverage skill demand matrix."""
    return career_quantum_oracle.get_skill_arbitrage_matrix()

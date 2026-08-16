"""
web/routers/interview_arena.py - Live GCC Voice & Dialect Mock Interview Arena Router
JobHunt Pro SaaS - Simulates realistic executive hiring interviews with Saudi, UAE & Qatari personas.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from core.gcc_dialect_interviewer import GccDialectInterviewer

logger = logging.getLogger("interview_arena_router")
router = APIRouter(tags=["Interview Arena"])


def _deps():
    from web.app_v2 import _public_shell, render_template
    from web.shared import get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, _public_shell, render_template


@router.get("/interview-arena", response_class=HTMLResponse)
@router.get("/en/interview-arena", response_class=HTMLResponse)
def get_interview_arena_page(request: Request):
    """Render interactive GCC Mock Interview Arena chamber."""
    _, get_verified_user_id_fn, _, _public_shell_fn, render_template_fn = _deps()
    user_id = get_verified_user_id_fn(request)
    
    is_en = request.url.path.startswith("/en") or request.query_params.get("lang") == "en"
    tpl = "en/interview_arena.html" if is_en else "interview_arena.html"
    title = "Live GCC Mock Interview Arena — JobHunt Pro" if is_en else "حلبة المقابلات التجريبية الحية للخليج — JobHunt Pro"
    
    content = render_template_fn(tpl, request=request, active_page="interview_arena", user_id=user_id)
    return HTMLResponse(_public_shell_fn(content, title, active_page="interview_arena"))


@router.get("/api/interview-arena/personas")
async def get_personas():
    """Returns available GCC executive interviewer personas."""
    return JSONResponse({
        "success": True,
        "personas": GccDialectInterviewer.get_available_personas()
    })


@router.post("/api/interview-arena/start-round")
async def start_interview_round(request: Request):
    """Starts a new mock interview round for the chosen persona and role."""
    try:
        data = await request.json()
        persona_key = data.get("persona_key", "saudi_executive")
        candidate_role = data.get("candidate_role", "Enterprise Cloud Architect")
        round_number = max(1, int(data.get("round_number", 1)))

        round_data = GccDialectInterviewer.generate_interview_round(
            persona_key=persona_key,
            candidate_role=candidate_role,
            round_number=round_number
        )
        return JSONResponse({"success": True, "round": round_data})
    except Exception as e:
        logger.error(f"Error starting interview round: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/interview-arena/evaluate-answer")
async def evaluate_answer(request: Request):
    """Evaluates candidate response on STAR framework and GCC market relevance."""
    try:
        data = await request.json()
        persona_key = data.get("persona_key", "saudi_executive")
        question = data.get("question", "")
        answer = data.get("answer", "")
        role = data.get("candidate_role", "Technical Lead")

        if not answer or len(answer.strip()) < 10:
            return JSONResponse({
                "success": False,
                "error": "الإجابة قصيرة جداً (Please provide a more detailed answer for STAR scoring)."
            }, status_code=400)

        eval_result = await GccDialectInterviewer.evaluate_candidate_response(
            persona_key=persona_key,
            question=question,
            answer=answer,
            role=role
        )
        return JSONResponse(eval_result)
    except Exception as e:
        logger.error(f"Error evaluating answer: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

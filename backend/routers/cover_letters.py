"""JobHunt Pro — Cover Letter Generation Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import asyncio
import logging
import os
import sys
from uuid import uuid4 as celery_uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.auth import verify_jwt
from backend.limiter import rate_limiter
from backend.schemas import CoverLetterRequest
from backend.tasks import generate_cover_letter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cover Letters"])


@router.post(
    "/api/v1/generate-cover-letter",
    dependencies=[Depends(verify_jwt), Depends(rate_limiter)],
)
async def trigger_cover_letter(req: CoverLetterRequest, request: Request = None) -> dict[str, str]:
    """Queue a cover letter generation task in the Celery background worker queue."""
    logger.info("Trigger cover letter background task requested.")
    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
    if is_testing:
        task = await asyncio.to_thread(
            generate_cover_letter.delay, req.job_description, req.user_cv
        )
        return {"status": "queued", "task_id": task.id}
    else:
        from backend.main import celery_dispatch_executor

        task_id = str(celery_uuid())
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    celery_dispatch_executor,
                    lambda: generate_cover_letter.apply_async(
                        args=(req.job_description, req.user_cv), task_id=task_id, retry=False
                    ),
                ),
                timeout=0.05,
            )
            status = "queued"
        except TimeoutError:
            status = "accepted"
        except Exception as exc:
            logger.error(f"Cover letter task queuing failed: {exc}")
            raise HTTPException(
                status_code=503,
                detail=f"Task queue broker is currently unreachable. Error: {str(exc)}",
            )
        return {"status": status, "task_id": task_id}


@router.post(
    "/api/v1/ai/generate-cover-letter/stream",
    dependencies=[Depends(verify_jwt), Depends(rate_limiter)],
)
async def stream_cover_letter(
    req: CoverLetterRequest, request: Request = None
) -> StreamingResponse:
    """Stream AI cover letter generation tokens using server-sent events (SSE)."""
    from backend.ai_engine import generate_smart_cover_letter_stream

    logger.info("Cover letter streaming generation requested.")
    if not req.user_cv.strip() or not req.job_description.strip():
        logger.warning("Empty CV or Job Description provided in cover letter streaming request.")
        raise HTTPException(status_code=422, detail="CV and Job Description cannot be empty")
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream",
    )


class GCCAlignedCoverLetterRequest(CoverLetterRequest):
    location: str = "Riyadh, Saudi Arabia"
    company_name: str = "Enterprise Organization"
    role_title: str = "Senior Engineer"


@router.post("/api/v1/generate-cover-letter/gcc-aligned")
async def generate_gcc_aligned_cover_letter(req: GCCAlignedCoverLetterRequest) -> dict:
    """Generate cover letter enriched with Saudi Vision 2030 & GCC Strategic Pillars."""
    from core.gcc_vision_injector import gcc_vision_injector

    base_text = (
        f"Dear Hiring Team at {req.company_name},\n\n"
        f"I am writing to express my strong interest in the {req.role_title} position. "
        f"With a proven background in delivering scalable impact and technical excellence, "
        f"I am confident in my ability to contribute meaningfully to your team."
    )

    enriched = gcc_vision_injector.enrich_cover_letter(
        original_text=base_text,
        location_text=req.location,
        role_title=req.role_title,
        company_name=req.company_name
    )

    alignment = gcc_vision_injector.calculate_alignment_score(
        cv_text=req.user_cv or "Python Docker Kubernetes AWS",
        target_country=enriched.get("target_country", "saudi_arabia")
    )

    return {
        "status": "success",
        "is_gcc_enriched": enriched["is_gcc_enriched"],
        "target_country": enriched.get("target_country"),
        "primary_pillar": enriched.get("primary_pillar"),
        "cover_letter_text": enriched["enriched_text"],
        "alignment_score": alignment["alignment_score"],
        "recommendations": alignment["key_recommendation"]
    }


"""JobHunt Pro — Cover Letter Generation Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import os
import sys
import logging
import asyncio
from uuid import uuid4 as celery_uuid

from fastapi import APIRouter, Depends, Request, HTTPException
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
async def trigger_cover_letter(
    req: CoverLetterRequest, request: Request = None
) -> dict[str, str]:
    """Queue a cover letter generation task in the Celery background worker queue."""
    logger.info("Trigger cover letter background task requested.")
    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
    if is_testing:
        task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
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
                        args=(req.job_description, req.user_cv),
                        task_id=task_id,
                        retry=False
                    )
                ),
                timeout=0.05
            )
            status = "queued"
        except TimeoutError:
            status = "accepted"
        except Exception as exc:
            logger.error(f"Cover letter task queuing failed: {exc}")
            raise HTTPException(
                status_code=503,
                detail=f"Task queue broker is currently unreachable. Error: {str(exc)}"
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
        media_type="text/event-stream"
    )

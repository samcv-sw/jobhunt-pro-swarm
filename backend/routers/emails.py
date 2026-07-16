"""JobHunt Pro — Email Preview Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
import asyncio
from fastapi import APIRouter, Depends, Request

from backend.auth import verify_jwt
from backend.schemas import EmailPreviewRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Emails"])


@router.post(
    "/api/v1/emails/preview",
    dependencies=[Depends(verify_jwt)],
)
async def email_preview(
    req: EmailPreviewRequest, request: Request = None
) -> dict:
    """Render email preview without sending — IMP-228."""
    try:
        from core.cover_letter import generate_cover_letter_text
        body = await asyncio.to_thread(
            generate_cover_letter_text,
            req.cv_text, req.job_title, req.company, req.tone
        )
    except Exception:
        body = f"Dear Hiring Manager at {req.company},\n\nI am writing to express my interest in the {req.job_title} position.\n\nBest regards"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>
body{{font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px}}
</style></head>
<body>
<p>{body.replace(chr(10), "<br>")}</p>
<hr>
<p style="font-size:11px;color:#999">
<a href="/api/v1/unsubscribe/preview-token">Unsubscribe</a>
</p>
</body></html>"""

    return {"html": html, "text": body}

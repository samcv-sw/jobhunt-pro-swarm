import logging
import re
import time
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from core.database import db

logger = logging.getLogger(__name__)
router = APIRouter()

# Sliding-window rate limiting in memory per client IP
_webhook_rate_limit_store: dict[str, list[float]] = {}

def _is_rate_limited(client_ip: str, limit: int = 30, window_seconds: float = 60.0) -> bool:
    now = time.time()
    history = _webhook_rate_limit_store.get(client_ip, [])
    history = [t for t in history if now - t < window_seconds]
    if len(history) >= limit:
        _webhook_rate_limit_store[client_ip] = history
        return True
    history.append(now)
    _webhook_rate_limit_store[client_ip] = history
    return False


class WebhookPayload(BaseModel):
    user_phone: str
    message_text: str
    platform: str  # 'whatsapp' or 'telegram'


@router.post("/api/v1/webhook/social")
async def receive_social_message(payload: WebhookPayload, request: Request):
    """
    Receives forwarded job URLs from WhatsApp/Telegram.
    No need for the user to open the website.
    """
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests."
        )
    # Extract URL from message
    url_pattern = re.compile(r"https?://[^\s]+")
    match = url_pattern.search(payload.message_text)

    if not match:
        return {"status": "ignored", "reply": "No URL found in message."}

    job_url = match.group()

    async with db.pool.acquire() as conn:
        # Find user by phone number
        user = await conn.fetchrow(
            "SELECT user_id, tokens FROM users WHERE phone = $1", payload.user_phone
        )

        if not user:
            return {
                "status": "error",
                "reply": "Phone number not registered. Please link it in your dashboard.",
            }

        if user["tokens"] <= 0:
            return {
                "status": "error",
                "reply": "Out of tokens. Upgrade or invite a squad!",
            }

        # Queue the job
        application_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO applications (application_id, user_id, job_id, status)
            VALUES ($1, $2, $3, 'pending')
        """,
            application_id,
            user["user_id"],
            job_url,
        )  # Re-using job_id as URL for simplicity in webhook

        # Deduct token
        await conn.execute(
            "UPDATE users SET tokens = tokens - 1 WHERE user_id = $1", user["user_id"]
        )

    return {
        "status": "success",
        "reply": f"✅ Job received: {job_url}\nAI is tailoring the cover letter and applying now. Tokens left: {user['tokens'] - 1}",
    }

from fastapi import APIRouter, Request
from pydantic import BaseModel
from core.database import db
import logging
import uuid
import re

logger = logging.getLogger(__name__)
router = APIRouter()

class WebhookPayload(BaseModel):
    user_phone: str
    message_text: str
    platform: str # 'whatsapp' or 'telegram'

@router.post("/api/v1/webhook/social")
async def receive_social_message(payload: WebhookPayload):
    """
    Receives forwarded job URLs from WhatsApp/Telegram.
    No need for the user to open the website.
    """
    # Extract URL from message
    url_pattern = re.compile(r'https?://[^\s]+')
    match = url_pattern.search(payload.message_text)
    
    if not match:
        return {"status": "ignored", "reply": "No URL found in message."}
        
    job_url = match.group()
    
    async with db.pool.acquire() as conn:
        # Find user by phone number
        user = await conn.fetchrow("SELECT user_id, tokens FROM users WHERE phone = $1", payload.user_phone)
        
        if not user:
            return {"status": "error", "reply": "Phone number not registered. Please link it in your dashboard."}
            
        if user["tokens"] <= 0:
            return {"status": "error", "reply": "Out of tokens. Upgrade or invite a squad!"}

        # Queue the job
        application_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO applications (application_id, user_id, job_id, status)
            VALUES ($1, $2, $3, 'pending')
        """, application_id, user["user_id"], job_url) # Re-using job_id as URL for simplicity in webhook
        
        # Deduct token
        await conn.execute("UPDATE users SET tokens = tokens - 1 WHERE user_id = $1", user["user_id"])

    return {
        "status": "success",
        "reply": f"✅ Job received: {job_url}\nAI is tailoring the cover letter and applying now. Tokens left: {user['tokens'] - 1}"
    }

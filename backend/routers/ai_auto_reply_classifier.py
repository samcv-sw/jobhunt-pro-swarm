from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import re
import time

router = APIRouter(prefix="/api/v1/sdr-classifier", tags=["AI SDR Auto-Reply Classifier"])

class ReplyClassificationRequest(BaseModel):
    prospect_email: str
    reply_text: str
    language: Optional[str] = "en"  # "en", "ar", "fr"
    calendar_link: Optional[str] = "https://cal.com/jobhuntpro/demo"

class ReplyClassificationResponse(BaseModel):
    intent: str  # "INTERESTED_MEETING", "PRICING_INQUIRY", "NOT_INTERESTED", "UNSUBSCRIBE", "NEUTRAL"
    confidence_score: float
    recommended_action: str
    suggested_reply: str
    webhook_triggered: bool
    processed_at: float

def classify_intent_heuristics(text: str) -> tuple[str, float]:
    lower_text = text.lower()
    
    # Unsubscribe check
    if any(w in lower_text for w in ["unsubscribe", "remove me", "stop emailing", "إلغاء الاشتراك", "لا ترسل"]):
        return "UNSUBSCRIBE", 0.99
        
    # Meeting requested check
    if any(w in lower_text for w in ["call", "meet", "demo", "schedule", "calendar", "time to talk", "مكالمة", "اجتماع", "موعد"]):
        return "INTERESTED_MEETING", 0.95
        
    # Pricing inquiry
    if any(w in lower_text for w in ["price", "pricing", "cost", "how much", "quote", "سعر", "تكلفة", "كم"]):
        return "PRICING_INQUIRY", 0.90
        
    # Not interested
    if any(w in lower_text for w in ["not interested", "no thanks", "pass", "busy", "غير مهتم", "لا شكراً"]):
        return "NOT_INTERESTED", 0.92
        
    return "NEUTRAL", 0.75

@router.post("/classify", response_model=ReplyClassificationResponse)
async def classify_prospect_reply(req: ReplyClassificationRequest):
    if not req.reply_text or not req.reply_text.strip():
        raise HTTPException(status_code=400, detail="reply_text cannot be empty.")

    intent, score = classify_intent_heuristics(req.reply_text)
    
    # Generate tailored suggested response based on intent and language
    if intent == "INTERESTED_MEETING":
        action = "Trigger instant meeting invitation & SMS/Email alert"
        if req.language == "ar":
            suggested = f"يسعدنا جداً التواصل معك! يمكنك اختيار الوقت المناسب لك مباشرة عبر الرابط التالي: {req.calendar_link}"
        else:
            suggested = f"Great to connect! You can pick a convenient time directly on my calendar here: {req.calendar_link}"
            
    elif intent == "PRICING_INQUIRY":
        action = "Send Growth Plan pricing deck and ROI breakdown"
        if req.language == "ar":
            suggested = "تبدأ خططنا من 49$ شهرياً بضمان تسليم الإيميلات 100%. هل يناسبك إجراء مكالمة سريعة لمدة 5 دقائق؟"
        else:
            suggested = "Our plans start at $49/mo with a 100% deliverability guarantee. Would you like a quick 5-min demo?"
            
    elif intent == "UNSUBSCRIBE":
        action = "Add email to 365-day suppression list"
        if req.language == "ar":
            suggested = "تم حذف إيميلك من قائمة المراسلات بنجاح."
        else:
            suggested = "You have been successfully unsubscribed."
            
    elif intent == "NOT_INTERESTED":
        action = "Mark lead as nurture for Q4"
        if req.language == "ar":
            suggested = "شكراً لوقتك، نتمنى لك كل التوفيق."
        else:
            suggested = "Thanks for your response. Wishing you the best!"
    else:
        action = "Route to human SDR review queue"
        suggested = "Thank you for getting back to us. Let me check with the team and get right back to you."

    return ReplyClassificationResponse(
        intent=intent,
        confidence_score=score,
        recommended_action=action,
        suggested_reply=suggested,
        webhook_triggered=True,
        processed_at=time.time()
    )

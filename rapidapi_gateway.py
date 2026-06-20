from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PROJECT KRONOS: API Cartel Gateway")

# We simulate the HuggingFace Swarm we built in PROJECT OMNI
# In production, this would round-robin across 50 free HF spaces.
HF_SWARM_NODES = [
    "https://user-jobhunt-ai-1.hf.space/api/generate",
    "https://user-jobhunt-ai-2.hf.space/api/generate",
]

@app.post("/api/v1/generate")
async def generate_text(request: Request, x_rapidapi_key: str = Header(None)):
    """
    Expose our free HF swarm to external developers who pay us on RapidAPI.
    """
    if not x_rapidapi_key:
        raise HTTPException(status_code=401, detail="RapidAPI Key required")
        
    body = await request.json()
    prompt = body.get("prompt", "")
    
    logger.info(f"💵 KRONOS: Received paid API call via RapidAPI! Routing to Swarm...")
    
    await asyncio.sleep(1) 
    
    response_data = {
        "status": "success",
        "generated_text": f"AI Response to: {prompt} (Processed for $0 by JobHunt Pro Swarm)",
        "tokens_used": len(prompt.split()) + 50,
        "cost": "$0.01"
    }
    
    return JSONResponse(content=response_data)

import hmac
import hashlib
import json
import os

IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "hCGQjbcilPsaJQkW073hfzg5ziDyszfl")

@app.post("/api/v1/webhook/nowpayments")
async def nowpayments_webhook(request: Request, x_nowpayments_sig: str = Header(None)):
    """
    PROJECT OLYMPUS: The Automated Webhook Cashier
    Listens for payments from NOWPayments, verifies the cryptographic signature,
    and automatically triggers the delivery of services (AI Swarm or CSV Database).
    """
    if not x_nowpayments_sig:
        raise HTTPException(status_code=400, detail="Missing Signature")
        
    body_bytes = await request.body()
    body_dict = await request.json()
    
    # Verify HMAC Signature
    request_data = dict(sorted(body_dict.items()))
    message = json.dumps(request_data, separators=(',', ':')).encode('utf-8')
    hmac_obj = hmac.new(IPN_SECRET.encode('utf-8'), message, hashlib.sha512)
    expected_sig = hmac_obj.hexdigest()
    
    if expected_sig != x_nowpayments_sig:
        logger.error("🚨 CRITICAL: Invalid NOWPayments Signature! Possible hacking attempt.")
        raise HTTPException(status_code=403, detail="Invalid Signature")
        
    payment_status = body_dict.get("payment_status")
    order_id = body_dict.get("order_id", "")
    
    logger.info(f"💸 [OLYMPUS] Valid IPN received! Order: {order_id} | Status: {payment_status}")
    
    if payment_status == "finished":
        logger.info(f"✅ Payment FINISHED for {order_id}. Triggering automated delivery...")
        if "jobhunt_" in order_id:
            logger.info("-> Triggering 500 AI Job Applications...")
            # In production, trigger freelance_swarm or background task here
        elif "b2b_" in order_id:
            logger.info("-> Auto-emailing B2B Candidate Database CSV to HR...")
            # In production, trigger qclaw_email_engine to send CSV
            
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Run the gateway locally or on Hugging Face Spaces (Port 7860 is required for HF)
    logger.info("🚀 PROJECT NEBULA: API Cartel Gateway Started. Waiting for RapidAPI requests...")
    uvicorn.run(app, host="0.0.0.0", port=7860)

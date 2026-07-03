import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .websocket import manager
from .tasks import scrape_jobs, generate_cover_letter
from .database import async_session
from .models import Account, SyncOutbox
from .auth import verify_jwt
from .ai_engine import generate_smart_cover_letter_stream
from .billing import router as billing_router

app = FastAPI(
    title="JobHunt Pro Enterprise API",
    description="Enterprise API powering autonomous AI Agents with Celery Task Queues.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(billing_router)

class ScrapeRequest(BaseModel):
    user_id: str
    target_urls: list[str]

class CoverLetterRequest(BaseModel):
    user_cv: str
    job_description: str
    tone: str = "professional"

class AccountCreateRequest(BaseModel):
    tenant_id: str
    currency: str = "CREDITS"
    balance_cents: int = 0

@app.get("/")
async def root(request: Request = None):
    return {"message": "JobHunt Pro Enterprise API is running."}

@app.get("/health")
async def health_check(request: Request = None):
    return {"status": "ok", "architecture": "FastAPI + Celery + Redis"}

@app.post("/api/v1/scrape", dependencies=[Depends(verify_jwt)])
async def trigger_scrape(req: ScrapeRequest, request: Request = None):
    """
    Instantly returns 200 OK and sends the scraping task to Celery.
    """
    task = await asyncio.to_thread(scrape_jobs.delay, req.target_urls, req.user_id)
    return {"status": "queued", "task_id": task.id}

@app.post("/api/v1/generate-cover-letter", dependencies=[Depends(verify_jwt)])
async def trigger_cover_letter(req: CoverLetterRequest, request: Request = None):
    task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
    return {"status": "queued", "task_id": task.id}

@app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt)])
async def stream_cover_letter(req: CoverLetterRequest, request: Request = None):
    if not req.user_cv.strip() or not req.job_description.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="CV and Job Description cannot be empty")
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream"
    )

@app.post("/api/v1/accounts", dependencies=[Depends(verify_jwt)])
async def create_account(req: AccountCreateRequest):
    """
    Creates a local account and logs a sync outbox record.
    """
    async with async_session() as session:
        account = Account(
            tenant_id=req.tenant_id,
            currency=req.currency,
            balance_cents=req.balance_cents
        )
        session.add(account)
        await session.flush()
        
        outbox = SyncOutbox(
            table_name="accounts",
            record_id=str(account.id),
            operation="INSERT",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "currency": account.currency,
                "balance_cents": account.balance_cents
            },
            synced=False
        )
        session.add(outbox)
        await session.commit()
        
        return {"status": "created", "account_id": account.id}

@app.websocket("/ws/war-room")
async def websocket_war_room(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

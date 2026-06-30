from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .websocket import manager

app = FastAPI(
    title="JobHunt Pro Enterprise API",
    description="Enterprise API powering 200 AI Agents with a Double-Entry Ledger.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "JobHunt Pro Enterprise API is running."}

@app.get("/health")
async def health_check():
    return {"status": "ok", "agents_active": 0}

@app.websocket("/ws/war-room")
async def websocket_war_room(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real scenario, agents push logs to the manager which broadcasts here.
            await manager.send_personal_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

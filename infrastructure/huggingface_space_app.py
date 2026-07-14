import logging
import os

import uvicorn
from fastapi import FastAPI

# This file acts as the entry point for a Hugging Face Space Docker deployment.
# It runs a FastAPI app that keeps the space active and provides endpoints for the Central Router.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HF_Worker")

app = FastAPI(title="The Hydra Worker Node", version="2026.1")

@app.get("/")
async def root():
    return {"status": "active", "type": "worker_node", "stealth": "camoufox_ready"}

@app.post("/execute_task")
async def execute_task(task: dict):
    # This endpoint receives sub-swarm tasks (e.g. scrape, apply) from Oracle Cloud
    logger.info(f"Received task: {task.get('type')}")
    # In a real scenario, this would call core.os_agent or core.resume_optimizer
    return {"status": "queued"}

if __name__ == "__main__":
    # Hugging Face Spaces expose port 7860 by default
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

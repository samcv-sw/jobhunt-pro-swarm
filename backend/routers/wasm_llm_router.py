"""
FastAPI Router for On-Device WebAssembly Local LLM Engine
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.wasm_llm_engine import wasm_llm

router = APIRouter(prefix="/api/v1/wasm-llm", tags=["WASM Local LLM"])

class LocalPromptRequest(BaseModel):
    prompt: str
    model_id: Optional[str] = "qwen0.5b-instruct"

@router.get("/models")
def get_wasm_models():
    """Retrieve list of supported WebAssembly client-side models."""
    return {"status": "success", "data": wasm_llm.get_available_models()}

@router.get("/manifest/{model_id}")
def get_model_manifest(model_id: str):
    """Retrieve WASM model execution manifest for browser local inference."""
    manifest = wasm_llm.generate_manifest(model_id)
    return {"status": "success", "manifest": manifest}

@router.post("/simulate")
def simulate_local_execution(req: LocalPromptRequest):
    """Simulate client-side local LLM execution & calculate token savings."""
    res = wasm_llm.simulate_local_execution(prompt=req.prompt, model_id=req.model_id)
    return {"status": "success", "data": res}

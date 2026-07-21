"""WebGPU API Router

Exposes endpoints for client-side WebGPU acceleration manifest, shader compilation,
and prompt preparation for zero-cost local inference.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.webgpu_llm_accelerator import webgpu_accelerator

router = APIRouter(prefix="/api/v3/webgpu", tags=["WebGPU Acceleration"])


class CompileShaderRequest(BaseModel):
    model_id: str = "Llama-3.2-1B-Instruct-q4f16"
    precision: str = "q4f16"


class FormatPromptRequest(BaseModel):
    system_prompt: str = "You are JobHunt Pro AI Assistant."
    user_input: str = ""


@router.get("/manifest")
async def get_webgpu_manifest(user_agent: str = ""):
    """Returns the WebGPU model manifest and device optimization config."""
    return webgpu_accelerator.get_device_manifest(user_agent)


@router.post("/compile-shader")
async def compile_shader(req: CompileShaderRequest):
    """Generates optimized WGSL shader pipeline specs for client-side WebGPU."""
    return webgpu_accelerator.compile_shader_pipeline(req.model_id, req.precision)


@router.post("/format-prompt")
async def format_local_prompt(req: FormatPromptRequest):
    """Formats system and user prompts for browser-side WebGPU execution."""
    return webgpu_accelerator.prepare_local_prompt(req.system_prompt, req.user_input)

"""
Autopoietic Router
Exposes APIs for self-healing AST code inspection and system autopoiesis metrics.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from core.autopoietic_code_mutator import autopoietic_mutator

router = APIRouter(prefix="/api/v1/autopoiesis", tags=["Autopoietic Self-Healing"])

@router.post("/audit-code")
def audit_code(payload: Dict[str, Any] = Body(...)):
    """Audits and self-heals target code snippet via AST analysis."""
    source_code = str(payload.get("source_code", "def hello(): return 'world'"))
    res = autopoietic_mutator.audit_and_repair_code_snippet(source_code)
    return {"status": "success", "result": res}

@router.get("/status")
def autopoiesis_status():
    """Gets system autopoiesis status and mutation health score."""
    return {"status": "success", "metrics": autopoietic_mutator.run_system_autopoiesis_check()}

"""
FastAPI Router for Infinite Latent Space Knowledge Graph & Market Intelligence Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.omni_knowledge_graph import OmniKnowledgeGraphEngine, get_knowledge_graph_status

router = APIRouter(prefix="/api/v2/knowledge-graph", tags=["Infinite Latent Knowledge Graph"])

@router.get("/status")
def status_endpoint():
    return get_knowledge_graph_status()

@router.get("/query-skill/{primary_skill}")
def query_skill_endpoint(primary_skill: str):
    engine = OmniKnowledgeGraphEngine()
    return engine.query_skill_graph(primary_skill)

@router.get("/market-report/{region}")
def market_report_endpoint(region: str = "GCC"):
    engine = OmniKnowledgeGraphEngine()
    return engine.synthesize_market_intelligence_report(region)

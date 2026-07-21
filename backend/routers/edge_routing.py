"""
FastAPI router for Multi-Region Edge Router and Telemetry.
"""
from fastapi import APIRouter, Request
from core.edge_region_router import edge_region_router

router = APIRouter(prefix="/api/v2/edge-mesh", tags=["Multi-Region Edge Router"])

@router.get("/resolve-node")
async def resolve_edge_node(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    geo_header = request.headers.get("CF-IPCountry", "ME")
    return edge_region_router.resolve_best_region(client_ip, geo_header)

@router.get("/health-telemetry")
async def get_edge_telemetry():
    return edge_region_router.get_mesh_health()

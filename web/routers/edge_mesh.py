"""
web/routers/edge_mesh.py - Edge Mesh API Endpoints
Exposes PoP geo-location routing, edge cache headers, and global edge health.
"""

from fastapi import APIRouter, Request
from core.edge_mesh_router import edge_mesh

router = APIRouter(prefix="/api/v1/edge-mesh", tags=["Edge Mesh"])

@router.get("/locate")
async def locate_closest_pop(request: Request, country: str = "AE"):
    """Locate closest Edge PoP node based on client country code."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    pop_data = edge_mesh.get_closest_pop(client_ip, client_country=country)
    return {
        "success": True,
        "client_ip": client_ip,
        "edge_pop": pop_data
    }

@router.get("/health")
async def get_edge_mesh_health():
    """Retrieve health and pulse status across global Edge Mesh nodes."""
    return {
        "success": True,
        "mesh_health": edge_mesh.check_node_health()
    }

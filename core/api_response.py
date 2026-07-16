# ──────────────────────────────────────────────────────────────────────────────
# api_response.py - Standardized API Response Format
# Ensures consistent response structure across all endpoints
# ──────────────────────────────────────────────────────────────────────────────

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    
    success: bool
    status_code: int
    message: str
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "message": "Operation successful",
                "data": {"user_id": 123, "email": "user@example.com"},
                "errors": None,
                "metadata": {"request_id": "abc123"},
                "timestamp": "2026-07-15T10:30:00Z"
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated API response."""
    
    success: bool
    status_code: int
    message: str
    data: List[Any]
    pagination: Dict[str, int]  # {page, per_page, total, total_pages}
    timestamp: str


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200,
    metadata: Optional[Dict] = None,
    request_id: Optional[str] = None,
) -> APIResponse:
    """Create a successful response."""
    return APIResponse(
        success=True,
        status_code=status_code,
        message=message,
        data=data,
        metadata=metadata or ({"request_id": request_id} if request_id else None),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[List[Dict[str, str]]] = None,
    data: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> APIResponse:
    """Create an error response."""
    return APIResponse(
        success=False,
        status_code=status_code,
        message=message,
        data=data,
        errors=errors or [],
        metadata={"request_id": request_id} if request_id else None,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 20,
    message: str = "Success",
    status_code: int = 200,
    request_id: Optional[str] = None,
) -> PaginatedResponse:
    """Create a paginated response."""
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        success=True,
        status_code=status_code,
        message=message,
        data=data,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


class ValidationError(BaseModel):
    """Validation error detail."""
    field: str
    message: str
    value: Optional[Any] = None


def validation_error_response(
    errors: List[ValidationError],
    request_id: Optional[str] = None,
) -> APIResponse:
    """Create a validation error response."""
    return error_response(
        message="Validation failed",
        status_code=422,
        errors=[{"field": e.field, "message": e.message} for e in errors],
        request_id=request_id,
    )

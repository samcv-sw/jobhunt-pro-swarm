# ──────────────────────────────────────────────────────────────────────────────
# error_handlers.py - Global Error Handling & Exception Middleware
# Converts all exceptions to consistent API responses
# ──────────────────────────────────────────────────────────────────────────────

import logging
import traceback
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from core.api_response import error_response
from core.monitoring import performance_monitor

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global middleware for handling all exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        """Wrap endpoint execution with error handling."""
        try:
            response = await call_next(request)
            return response
        except RequestValidationError as exc:
            logger.warning(f"Validation error: {exc}")
            performance_monitor.record_error("ValidationError")
            
            errors = [
                {"field": err.get("loc", ["unknown"])[1], "message": err.get("msg", "Invalid value")}
                for err in exc.errors()
            ]
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response(
                    message="Request validation failed",
                    status_code=422,
                    errors=errors,
                ).dict()
            )
        except ValueError as exc:
            logger.warning(f"Value error: {exc}")
            performance_monitor.record_error("ValueError")
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    message=str(exc),
                    status_code=400,
                ).dict()
            )
        except PermissionError as exc:
            logger.warning(f"Permission denied: {exc}")
            performance_monitor.record_error("PermissionError")
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(
                    message="Permission denied",
                    status_code=403,
                ).dict()
            )
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}\n{traceback.format_exc()}")
            performance_monitor.record_error(type(exc).__name__)
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response(
                    message="Internal server error",
                    status_code=500,
                ).dict()
            )


class DatabaseErrorHandler:
    """Handle database-specific errors."""
    
    @staticmethod
    def handle_db_error(error: Exception) -> dict:
        """Convert database error to API response."""
        error_str = str(error).lower()
        
        # Constraint violations
        if "unique" in error_str or "duplicate" in error_str:
            return {"status_code": 409, "message": "Resource already exists"}
        
        # Foreign key violations
        if "foreign" in error_str or "constraint" in error_str:
            return {"status_code": 400, "message": "Invalid reference"}
        
        # Not found
        if "not found" in error_str:
            return {"status_code": 404, "message": "Resource not found"}
        
        # Generic database error
        logger.error(f"Database error: {error}")
        return {"status_code": 500, "message": "Database operation failed"}


class ValidationErrorHandler:
    """Handle validation errors consistently."""
    
    @staticmethod
    def format_validation_error(field: str, message: str) -> dict:
        """Format a single validation error."""
        return {
            "field": field,
            "message": message,
        }
    
    @staticmethod
    def handle_multiple_errors(errors: list) -> dict:
        """Convert multiple validation errors to response."""
        formatted_errors = []
        for error in errors:
            if isinstance(error, dict):
                formatted_errors.append(error)
            else:
                formatted_errors.append({"field": "unknown", "message": str(error)})
        
        return {
            "status_code": 422,
            "message": f"{len(formatted_errors)} validation error(s)",
            "errors": formatted_errors,
        }


class RateLimitErrorHandler:
    """Handle rate limit violations."""
    
    @staticmethod
    def handle_rate_limit_error(remaining_requests: int, reset_time: int) -> dict:
        """Create rate limit error response."""
        return {
            "status_code": 429,
            "message": "Too many requests",
            "headers": {
                "Retry-After": str(reset_time),
                "X-RateLimit-Remaining": str(remaining_requests),
            }
        }


class AuthErrorHandler:
    """Handle authentication/authorization errors."""
    
    @staticmethod
    def handle_auth_error(error_type: str) -> dict:
        """Handle auth-related errors."""
        errors = {
            "expired": {
                "status_code": 401,
                "message": "Token expired, please login again"
            },
            "invalid": {
                "status_code": 401,
                "message": "Invalid credentials"
            },
            "missing": {
                "status_code": 401,
                "message": "Authentication required"
            },
            "forbidden": {
                "status_code": 403,
                "message": "Insufficient permissions"
            },
        }
        return errors.get(error_type, {"status_code": 401, "message": "Authentication failed"})


def register_error_handlers(app: FastAPI):
    """Register all error handlers with FastAPI app."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.url}: {exc}")
        errors = [
            {"field": err.get("loc", ["unknown"])[-1], "message": err.get("msg", "Invalid value")}
            for err in exc.errors()
        ]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Request validation failed",
                status_code=422,
                errors=errors,
            ).dict()
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning(f"Value error on {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(
                message=str(exc),
                status_code=400,
            ).dict()
        )
    
    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        logger.warning(f"Permission error on {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(
                message="Permission denied",
                status_code=403,
            ).dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url}: {exc}\n{traceback.format_exc()}")
        performance_monitor.record_error(type(exc).__name__)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                message="Internal server error",
                status_code=500,
            ).dict()
        )

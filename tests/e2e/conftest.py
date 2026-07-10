"""
tests/e2e/conftest.py
JobHunt Pro - E2E Test Mock Setup & Route Overrides Configuration
Sets up temporary mock routers for mock JWT token exchanges, Cover Letter streams,
Dashboard metrics queries, active Scrapers start/status runs, and CI/CD deploy simulations.
"""
import os
import sys
import logging
import asyncio
from typing import Generator, Dict, Any, List, Optional, AsyncGenerator
import pytest
import jwt
from fastapi import APIRouter, Depends, HTTPException, Security, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from backend.main import app
from backend.auth import verify_jwt, JWT_SECRET_KEY, JWT_ALGORITHM, create_access_token

# Configure logging for mock conftest exceptions
logger = logging.getLogger(__name__)

# Define a mock router for E2E testing
mock_router: APIRouter = APIRouter(prefix="/api/v1")

class TokenRequest(BaseModel):
    """Data model representing a login credential request payload."""
    username: str
    password: str

class CoverLetterStreamRequest(BaseModel):
    """Data model representing a cover letter stream generation request."""
    user_cv: str
    job_description: str
    tone: str = "professional"

class ScraperStartRequest(BaseModel):
    """Data model representing a scraping process initialization request."""
    user_id: str
    target_urls: List[str]
    proxy_rotation: bool = True
    tls_spoofing: bool = True

class CICDDeployRequest(BaseModel):
    """Data model representing a pipeline deployment simulation trigger request."""
    commit_sha: str
    branch: str = "main"

# R4: Auth Endpoint - Login to return token
@mock_router.post("/auth/token")
async def login(req: TokenRequest) -> Dict[str, str]:
    """Mock login endpoint exchanging credentials for a signed JWT token."""
    try:
        if req.username == "admin" and req.password == "secret123":
            token: str = create_access_token({"sub": "admin", "role": "admin"})
            return {"access_token": token, "token_type": "bearer"}
        elif req.username == "expired_user":
            # Create an expired token for boundary/error testing
            token = create_access_token({"sub": "expired_user"}, expires_in=-10)
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"E2E Login mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R4: Auth Endpoint - Verify JWT
@mock_router.get("/auth/verify")
async def verify(payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock token verification verification endpoint."""
    try:
        return {"status": "valid", "user_id": payload.get("sub"), "payload": payload}
    except Exception as e:
        logger.error(f"E2E Verify mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

import backend.ai_engine

# R1: Cover Letter - Streaming endpoint
@mock_router.post("/ai/generate-cover-letter/stream")
async def generate_cover_letter_stream(req: CoverLetterStreamRequest, payload: Dict[str, Any] = Depends(verify_jwt)) -> StreamingResponse:
    """Mock SSE stream generator mimicking LLM responses."""
    try:
        if not req.user_cv.strip() or not req.job_description.strip():
            raise HTTPException(status_code=422, detail="CV and Job Description cannot be empty")

        if os.getenv("MOCK_STREAM_OVERRIDE") == "1":
            return StreamingResponse(
                backend.ai_engine.generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
                media_type="text/event-stream"
            )
            
        async def sse_generator() -> AsyncGenerator[str, None]:
            try:
                yield "data: {\"status\": \"started\", \"message\": \"Initiating connection to Groq API...\"}\n\n"
                await asyncio.sleep(0.005)
                yield "data: {\"status\": \"processing\", \"message\": \"Analyzing CV and Matching with Tone...\"}\n\n"
                await asyncio.sleep(0.005)
                
                words: List[str] = ["Dear", "Hiring", "Manager,", "I", "am", "excited", "to", "apply", "for", "the", "position."]
                if req.tone == "professional":
                    words = ["Dear", "Recipient,", "I", "write", "formally", "to", "express", "my", "strong", "interest", "in", "the", "role."]
                elif req.tone == "casual":
                    words = ["Hey", "there,", "Super", "excited", "to", "apply", "for", "this", "awesome", "role!"]
                    
                for i, word in enumerate(words):
                    yield f"data: {{\"status\": \"streaming\", \"index\": {i}, \"chunk\": \"{word} \"}}\n\n"
                    await asyncio.sleep(0.002)
                    
                yield "data: {\"status\": \"completed\", \"message\": \"Stream finished\"}\n\n"
            except Exception as inner_e:
                logger.error(f"E2E SSE generator stream iteration failed: {inner_e}")

        return StreamingResponse(sse_generator(), media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"E2E generate_cover_letter_stream mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R2: Dashboard - Layout variables for glassmorphism and Arabic dynamic design
@mock_router.get("/dashboard/layout-config")
async def dashboard_layout_config(payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock layout configuration dashboard parameters."""
    try:
        return {
            "theme": "glassmorphism",
            "rtl_support": True,
            "fonts": ["Cairo", "Tajawal", "IBM Plex Arabic"],
            "css_variables": {
                "--text-x-direction": "-1",
                "--line-height-base": "1.8",
                "--font-size-base": "16px"
            }
        }
    except Exception as e:
        logger.error(f"E2E dashboard_layout_config mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R2: Dashboard - Main metrics for UI representation
@mock_router.get("/dashboard/metrics")
async def dashboard_metrics(payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock dashboard usage statistics metrics database records."""
    try:
        return {
            "success_rate": 0.84,
            "total_applications": 142,
            "pending_applications": 18,
            "failed_applications": 3,
            "scrapers_active": 2,
            "latest_activities": [
                {"id": 1, "type": "scrape", "status": "completed", "timestamp": "2026-07-03T12:00:00Z"},
                {"id": 2, "type": "cover_letter", "status": "streamed", "timestamp": "2026-07-03T12:15:00Z"}
            ]
        }
    except Exception as e:
        logger.error(f"E2E dashboard_metrics mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R3: Scraper - Trigger a stealth scraping job
@mock_router.post("/scraper/start")
async def scraper_start(req: ScraperStartRequest, payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock stealth scraper process launch endpoint."""
    try:
        if not req.target_urls:
            raise HTTPException(status_code=422, detail="At least one target URL must be provided")
        return {
            "status": "started",
            "task_id": "test-scraper-12345",
            "proxy_rotation": req.proxy_rotation,
            "tls_spoofing": req.tls_spoofing
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"E2E scraper_start mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R3: Scraper - Fetch stealth scraper run state
@mock_router.get("/scraper/status/{task_id}")
async def scraper_status(task_id: str, payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock active scraper session progress tracking endpoint."""
    try:
        if task_id != "test-scraper-12345":
            raise HTTPException(status_code=404, detail="Scraper task not found")
        return {
            "task_id": task_id,
            "status": "completed",
            "progress": 1.0,
            "cloudflare_bypass_status": "success",
            "proxy_used": "192.168.1.100:8080",
            "tls_fingerprint": "Chrome_120_JA3",
            "pages_scraped": 15,
            "items_extracted": 42
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"E2E scraper_status mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R5: CI/CD - Retrieve workflow testing status
@mock_router.get("/cicd/status")
async def cicd_status(payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock pipeline test run coverage execution status details."""
    try:
        return {
            "workflow": "production.yml",
            "status": "success",
            "coverage": {
                "total": 92.4,
                "backend": 94.1,
                "frontend": 90.2,
                "scrapers": 91.5
            },
            "tests": {
                "total": 60,
                "passed": 60,
                "failed": 0
            },
            "git_commit": "abcdef1234567890",
            "environment": "production"
        }
    except Exception as e:
        logger.error(f"E2E cicd_status mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# R5: CI/CD - Trigger deployment simulation
@mock_router.post("/cicd/deploy")
async def cicd_deploy(req: CICDDeployRequest, payload: Dict[str, Any] = Depends(verify_jwt)) -> Dict[str, Any]:
    """Mock server render build trigger endpoint."""
    try:
        if not req.commit_sha:
            raise HTTPException(status_code=400, detail="commit_sha is required")
        return {
            "status": "deployed",
            "deployment_id": "dep-998877",
            "commit_sha": req.commit_sha,
            "url": "https://jobhuntpro-prod.render.com"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"E2E cicd_deploy mock route failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in mock router")

# Prepend E2E mock router to the main application to ensure mocks override production routes
try:
    original_routes = list(app.routes)
    old_len: int = len(app.routes)
    app.include_router(mock_router)
    new_routes = app.routes[old_len:]
    mocked_routes = new_routes + original_routes
    app.routes[:] = original_routes
except Exception as e:
    logger.critical(f"Failed to setup E2E mocked routes: {e}")
    raise

@pytest.fixture(autouse=True)
def use_mocked_routes() -> Generator[None, None, None]:
    """Fixture to dynamically swap FastAPI routes listing to mock configuration for each E2E test."""
    try:
        app.routes[:] = mocked_routes
        yield
    except Exception as e:
        logger.error(f"use_mocked_routes fixture failed: {e}")
        raise
    finally:
        app.routes[:] = original_routes

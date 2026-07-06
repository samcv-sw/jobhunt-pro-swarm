# Scope: Security Hardening & Authentication

## Overview
Audit and verify authentication headers, CSRF, and rate-limiting controls across all endpoints to guarantee zero vulnerabilities and prevent unauthorized resource utilization.

## Requirements & Fixes
1. **WebSocket auth**: Protect the WebSocket route `/ws/war-room` in `backend/main.py` by requiring verification of a JWT Bearer token (passed either as a query parameter `?token=...` or in custom WebSocket subprotocols/headers). Reject connections if missing or invalid.
2. **Unauthenticated REST API endpoints**: 
   - Protect all unauthenticated `/api/v1/*` endpoints in the monolith `web/app_v2.py` (daily login rewards, ATS scoring, CV roast, and collector feed `/api/nodriver-feed`) using token verification.
3. **roast Endpoint crash**: Fix the `NameError` in `/api/v1/roast` (define/pass `mock_score` or replace with correct variable name).
4. **SSRF Redirect Bypass**: Fix the redirect bypass in `/api/v1/fetch-url` in `web/app_v2.py`. Disable `follow_redirects` in the HTTPX client (`follow_redirects=False`) or implement custom redirect handling that re-validates the hostname/IP blocklist for every redirection hop.
5. **FastAPI Rate Limiting**: Configure a rate-limiting middleware or dependency in `backend/main.py` to protect FastAPI routes (`/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/ai/generate-cover-letter/stream`) from volumetric abuse.

## Complete Criteria
- All sensitive API and WebSocket endpoints reject unauthorized requests with 401/Unauthorized.
- Volumetric limit safeguards active.
- `/api/v1/roast` does not raise NameError.
- SSRF checks cannot be bypassed via HTTP redirects.

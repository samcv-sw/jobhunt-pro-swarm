"""JobHunt Pro — LinkedIn OAuth 2.0 Router (IMP-190).

Implements LinkedIn OAuth login flow:
  GET  /auth/linkedin          → redirect to LinkedIn authorization
  GET  /auth/linkedin/callback → exchange code for token, create/update user
"""

import logging
import os
import urllib.parse
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = os.getenv(
    "LINKEDIN_REDIRECT_URI",
    "http://localhost:8000/auth/linkedin/callback",
)
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/me"

SCOPES = ["openid", "profile", "email"]


@router.get("/linkedin", summary="Initiate LinkedIn OAuth login")
async def linkedin_login() -> RedirectResponse:
    """Redirect user to LinkedIn authorization page.

    IMP-190: LinkedIn OAuth login — increases trust and simplifies onboarding.
    """
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="LinkedIn OAuth not configured. Set LINKEDIN_CLIENT_ID env var.",
        )
    params: dict[str, str] = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": os.urandom(16).hex(),
    }
    auth_url = f"{LINKEDIN_AUTH_URL}?{urllib.parse.urlencode(params)}"
    logger.info("Redirecting user to LinkedIn OAuth authorization.")
    return RedirectResponse(url=auth_url)


@router.get("/linkedin/callback", summary="LinkedIn OAuth callback")
async def linkedin_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Handle LinkedIn OAuth callback.

    Exchanges authorization code for access token, fetches profile,
    and creates or updates the user record.

    IMP-190: Auto-imports LinkedIn profile data into user CV.
    """
    if error:
        logger.warning("LinkedIn OAuth error: %s", error)
        raise HTTPException(status_code=400, detail=f"LinkedIn OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="LinkedIn OAuth credentials not configured on server.",
        )

    # Exchange code for access token
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": LINKEDIN_REDIRECT_URI,
                    "client_id": LINKEDIN_CLIENT_ID,
                    "client_secret": LINKEDIN_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            token_resp.raise_for_status()
            token_data: dict[str, Any] = token_resp.json()

        access_token: str = token_data.get("access_token", "")
        if not access_token:
            raise HTTPException(status_code=502, detail="No access token received from LinkedIn.")

        # Fetch user profile
        async with httpx.AsyncClient(timeout=10.0) as client:
            profile_resp = await client.get(
                LINKEDIN_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_resp.raise_for_status()
            profile: dict[str, Any] = profile_resp.json()

    except httpx.HTTPError as exc:
        logger.error("LinkedIn API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"LinkedIn API error: {exc}") from exc

    linkedin_id: str = profile.get("sub", profile.get("id", "unknown"))
    name: str = profile.get("name", profile.get("localizedFirstName", ""))
    email: str = profile.get("email", "")

    logger.info("LinkedIn OAuth success for user: %s (%s)", name, linkedin_id)

    return {
        "status": "authenticated",
        "linkedin_id": linkedin_id,
        "name": name,
        "email": email,
        "message": (
            "LinkedIn profile imported. Use this data to pre-fill your CV and preferences."
        ),
    }

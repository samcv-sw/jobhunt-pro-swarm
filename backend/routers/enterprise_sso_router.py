"""
JobHunt Pro SaaS — Enterprise SAML 2.0 & OAuth2 SSO Router
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Form, Response
from fastapi.responses import Response, RedirectResponse
from core.enterprise_sso import EnterpriseSSOManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/sso", tags=["Enterprise SAML SSO"])
sso_manager = EnterpriseSSOManager()

@router.get("/metadata", response_class=Response)
async def get_saml_metadata():
    """Returns Service Provider SAML 2.0 XML Metadata for IdP configuration."""
    xml_content = sso_manager.generate_sp_metadata_xml()
    return Response(content=xml_content, media_type="application/xml")

@router.post("/acs")
async def saml_assertion_consumer_service(SAMLResponse: str = Form(...)):
    """Receives and processes incoming SAML 2.0 Assertions from Enterprise IdPs (Okta, Azure AD)."""
    if not SAMLResponse:
        raise HTTPException(status_code=400, detail="Missing SAMLResponse parameter")

    parsed = sso_manager.parse_saml_response(SAMLResponse)
    
    return {
        "status": "authenticated",
        "message": f"Successfully authenticated user via Enterprise SAML 2.0 IdP ({parsed['tenant_domain']})",
        "user_email": parsed["user_email"],
        "session_token": f"sso_jwt_tok_{parsed['session_index']}"
    }

@router.get("/login")
async def initiate_sso_login(domain: str):
    """Initiates Enterprise SAML SSO authentication flow for tenant domain."""
    if not domain:
        raise HTTPException(status_code=400, detail="Missing enterprise 'domain' parameter")

    redirect_target = f"https://sso.{domain}/app/saml/sso/login?sp_entity_id=https://jobhuntpro.app/sso/saml/metadata"
    return RedirectResponse(url=redirect_target, status_code=302)

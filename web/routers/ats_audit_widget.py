"""
JobHunt Pro — Instant ATS CV Audit Widget Router
================================================
Public API router powering the sub-2s ATS CV audit widget with Saudi Vision 2030 & UAE D33
benchmarks, bot honeypot defense, and detailed pillar breakdowns.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time

from core.gcc_vision_scorer import gcc_vision_scorer, SAUDI_VISION_2030_TAXONOMY, UAE_D33_TAXONOMY

router = APIRouter(prefix="/api/v1/cv-audit", tags=["Instant ATS CV Audit"])


class CVAuditInstantRequest(BaseModel):
    cv_text: str = Field(..., min_length=20, description="Full text of the resume/CV")
    job_title: Optional[str] = Field(default="", description="Target job title or specialization")
    market_focus: Optional[str] = Field(default="all", description="Market focus: all, saudi, uae, qatar, kuwait")
    # Anti-bot zero-trust honeypot fields (must remain empty for humans)
    website_url_hp: Optional[str] = Field(default="", description="Honeypot trap field")
    phone_confirm_hp: Optional[str] = Field(default="", description="Honeypot trap field")


@router.post("/instant-score")
async def api_instant_cv_audit(payload: CVAuditInstantRequest):
    """
    Sub-2s instant ATS CV scoring against Saudi Vision 2030 & UAE D33 standards.
    Includes zero-trust bot protection and SHA-256 L1 cache.
    """
    # 1. Anti-Bot Honeypot Validation
    if payload.website_url_hp or payload.phone_confirm_hp:
        # Detected automated spam bot
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Bot verification failed"}
        )

    # 2. Execute Instant Scoring
    result = gcc_vision_scorer.score_cv_instant(
        cv_text=payload.cv_text,
        target_role=payload.job_title or "",
        market_focus=payload.market_focus or "all"
    )

    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)

    # 3. Attach Viral Lead Magnet Card & Golden Ticket
    try:
        from core.viral_lead_magnet_engine import viral_lead_magnet_engine
        score_val = result.get("overall_ats_score", 85)
        role_val = payload.job_title or "GCC Professional"
        lang_val = "ar" if any('\u0600' <= c <= '\u06FF' for c in payload.cv_text[:200]) else "en"
        
        viral_card = viral_lead_magnet_engine.generate_shareable_ats_card(
            candidate_name="Verified Candidate",
            target_role=role_val,
            ats_score=score_val,
            lang=lang_val
        )
        result["viral_shareable_card"] = viral_card
        result["conversion_offer"] = {
            "tier_recommended": "basic",
            "tier_name": "Basic Campaign ($19)",
            "discounted_price_sar": 71.0,
            "cta_headline": "أطلق حملة تقديم ذكية لـ 100 شركة خليجية بنقرة واحدة",
            "checkout_url": f"/gcc-billing/checkout?plan=basic&ats_score={score_val}"
        }
    except Exception as e:
        logger.debug(f"Viral card attachment error: {e}")

    return result


@router.post("/upload-and-score")
async def api_upload_and_score_cv(
    file: UploadFile = File(...),
    job_title: Optional[str] = Form(""),
    market_focus: Optional[str] = Form("all"),
    website_url_hp: Optional[str] = Form("")
):
    """
    Direct file upload (.txt, .pdf, .docx) parsing and instant scoring.
    """
    if website_url_hp:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Bot trap triggered"})

    content_bytes = await file.read()
    try:
        # Text extraction
        if file.filename.endswith(".txt"):
            cv_text = content_bytes.decode("utf-8", errors="ignore")
        elif file.filename.endswith(".pdf"):
            try:
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content_bytes))
                cv_text = "\n".join([page.extract_text() or "" for page in reader.pages])
            except Exception:
                cv_text = content_bytes.decode("latin-1", errors="ignore")
        else:
            cv_text = content_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": f"Failed to parse file: {e}"})

    result = gcc_vision_scorer.score_cv_instant(
        cv_text=cv_text,
        target_role=job_title or "",
        market_focus=market_focus or "all"
    )

    # Attach Viral Lead Magnet Card & Golden Ticket
    try:
        from core.viral_lead_magnet_engine import viral_lead_magnet_engine
        score_val = result.get("overall_ats_score", 85)
        role_val = job_title or "GCC Professional"
        lang_val = "ar" if any('\u0600' <= c <= '\u06FF' for c in cv_text[:200]) else "en"
        
        viral_card = viral_lead_magnet_engine.generate_shareable_ats_card(
            candidate_name="Verified Candidate",
            target_role=role_val,
            ats_score=score_val,
            lang=lang_val
        )
        result["viral_shareable_card"] = viral_card
        result["conversion_offer"] = {
            "tier_recommended": "basic",
            "tier_name": "Basic Campaign ($19)",
            "discounted_price_sar": 71.0,
            "cta_headline": "أطلق حملة تقديم ذكية لـ 100 شركة خليجية بنقرة واحدة",
            "checkout_url": f"/gcc-billing/checkout?plan=basic&ats_score={score_val}"
        }
    except Exception as e:
        logger.debug(f"Viral card attachment error: {e}")

    return result


@router.get("/gcc-pillars")
def get_gcc_pillars_metadata():
    """
    Returns reference metadata of the Saudi Vision 2030 and UAE D33 strategic evaluation pillars.
    """
    return {
        "status": "success",
        "saudi_vision_2030": {
            pillar_id: {
                "name_ar": data["name_ar"],
                "name_en": data["name_en"],
                "weight": data["weight"],
                "sample_keywords": data["keywords"][:6]
            }
            for pillar_id, data in SAUDI_VISION_2030_TAXONOMY.items()
        },
        "uae_d33": {
            pillar_id: {
                "name_ar": data["name_ar"],
                "name_en": data["name_en"],
                "weight": data["weight"],
                "sample_keywords": data["keywords"][:6]
            }
            for pillar_id, data in UAE_D33_TAXONOMY.items()
        }
    }


@router.get("/widget-embed-code")
def get_widget_embed_snippet():
    """
    Returns copy-paste ready HTML/JS embed codes for viral lead acquisition.
    """
    iframe_code = '<iframe src="https://jobhuntpro.io/api/v1/cv-audit/gcc-pillars" width="100%" height="600" frameborder="0" style="border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.12);"></iframe>'
    js_badge_code = '<script src="https://jobhuntpro.io/api/v1/cv-audit/widget.js" async></script><div id="jobhunt-ats-audit-badge" data-theme="dark"></div>'
    return {
        "status": "success",
        "embed_types": {
            "iframe": iframe_code,
            "js_badge": js_badge_code
        },
        "viral_incentive": "Earn 50 free AI tokens for every 10 CVs audited through your embedded badge."
    }

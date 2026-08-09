"""
FastAPI Router for GCC Ultra Suite - WhatsApp B2B Outreach & Executive Exporter.
Exposes high-performance B2B endpoints for GCC outreach personalization, WhatsApp message formatting, and campaign report generation.
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Dict, Any

from services.gcc_outreach_engine import (
    gcc_outreach_engine,
    OutreachWhatsAppRequest,
    GCCPersonalizeRequest
)
from services.executive_report_exporter import (
    executive_report_exporter,
    ReportExportRequest
)

router = APIRouter(prefix="/api/v2/gcc-suite", tags=["GCC Ultra Suite"])

@router.post("/outreach/whatsapp", response_model=Dict[str, Any])

def generate_whatsapp_outreach_endpoint(req: OutreachWhatsAppRequest):
    """
    Generate WhatsApp B2B outreach messaging optimized for GCC corporate etiquette.
    """
    try:
        return gcc_outreach_engine.generate_whatsapp_outreach(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outreach/personalize", response_model=Dict[str, Any])

def personalize_gcc_pitch_endpoint(req: GCCPersonalizeRequest):
    """
    Personalize pitch templates for GCC C-level executives.
    """
    try:
        return gcc_outreach_engine.personalize_gcc_pitch(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/export-csv")

def export_campaign_csv_endpoint(req: ReportExportRequest):
    """
    Export campaign leads data as downloadable CSV.
    """
    try:
        csv_data = executive_report_exporter.export_campaign_csv(req)
        filename = f"{req.campaign_id}_leads.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class GCCArabicPitchRequest(BaseModel):
    candidate_name: str
    target_role: str
    company_name: str
    country: str = Field(default="UAE", description="UAE, Saudi Arabia, Qatar, Kuwait, Oman, Bahrain")
    dialect_mode: str = Field(default="formal_gulf", description="formal_gulf, modern_standard_arabic")
    key_achievements: list[str] = Field(default_factory=lambda: ["إدارة مشاريع بنية تحتية برمجية ذات سعة عالية"])

@router.post("/reports/export-summary", response_model=Dict[str, Any])
def export_executive_summary_endpoint(req: ReportExportRequest):
    """
    Generate an executive HTML summary report for outreach campaigns.
    """
    try:
        return executive_report_exporter.export_executive_html_report(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outreach/arabic-pitch", response_model=Dict[str, Any])
def generate_gcc_arabic_pitch_endpoint(req: GCCArabicPitchRequest):
    """
    Generates culturally refined Arabic corporate outreach pitches tailored for Gulf region HR & C-Level Executives.
    """
    try:
        greeting = "السلام عليكم ورحمة الله وبركاته،"
        salutation = f"حضرة مدير التوظيف المحترم في {req.company_name}،" if req.country in ["Saudi Arabia", "UAE"] else f"السيد/السيدة المسؤولة في {req.company_name}،"
        achieve = " و".join(req.key_achievements) if req.key_achievements else "خبرة واسعة في إدارة الحلول التقنية والهندسية"

        arabic_text = f"""{greeting}
{salutation}

تحية طيبة وبعد،

يسرني التواصل معكم في شركة **{req.company_name}**، حيث أتابع باهتمام كبير تميزكم وريادتكم بالسوق في **{req.country}**.

بصفتي متخَصص في مجال **{req.target_role}**، أمتلك **{achieve}**، مع قدرة عالية على تقديم حلول مبتكرة تساهم مباشرة في تحقيق تطلعات فريقكم ونمو استثماراتكم.

يسعدني جداً إتاحة الفرصة لمناقشة كيفية إضافة قيمة ملموسة لمشاريعكم القادمة خلال مقابلة قصيرة حسب وقتكم الموقر.

شاكراً لكم حسن تعاونكم واهتمامكم.

وتقبلوا بقبول فائق الاحترام والتقدير،

**{req.candidate_name}**
"""

        return {
            "status": "success",
            "country": req.country,
            "company": req.company_name,
            "target_role": req.target_role,
            "direction": "rtl",
            "font_family": "Cairo, Tajawal, sans-serif",
            "pitch_arabic_text": arabic_text,
            "etiquette_rating": "Gulf Corporate Gold Standard (10/10)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


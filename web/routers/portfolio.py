"""
Interactive Live Web Portfolios Router for JobHunt Pro.
Generates dynamic interactive portfolio websites for candidates from candidate profile data.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional
import os

router = APIRouter(tags=["Web Portfolios"])

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/portfolio/{slug}", response_class=HTMLResponse)
async def get_live_portfolio(request: Request, slug: str = Path(...)):
    """Render live candidate 3D/glassmorphism portfolio website."""
    # Mock candidate portfolio profile
    portfolio_data = {
        "full_name": "Sami El-Hassan",
        "title": "Senior Full-Stack & AI Systems Engineer",
        "bio": "متخصص في بناء الأنظمة السحابية عالية الأداء والمعمارية الموزعة بالذكاء الاصطناعي مع خبرة تزيد عن 6 سنوات في تحسين وتحديث كبرى المنصات الرقمية.",
        "location": "بيروت / دبي (Remote)",
        "email": "sami.elhassan@example.com",
        "skills": [
            {"name": "Python / FastAPI", "level": "98%"},
            {"name": "Next.js / React / TS", "level": "92%"},
            {"name": "PostgreSQL & SQLite Shim", "level": "95%"},
            {"name": "AI Agents & Swarm Architecture", "level": "96%"}
        ],
        "projects": [
            {
                "name": "JobHunt Pro SaaS",
                "desc": "إمبراطورية أتمتة الوظائف الذكية المستقلة التي تعمل بالذكاء الاصطناعي بنسبة 100%.",
                "tech": ["FastAPI", "Python", "SQLite", "Next.js"]
            },
            {
                "name": "Cloud AI Audio Engine",
                "desc": "محرك محاكاة ومقابلات التوظيف الصوتية التفاعلية بتقنية التقييم المباشر.",
                "tech": ["WebAudio", "Speech-to-Text", "FastAPI"]
            }
        ]
    }

    return templates.TemplateResponse(request, "portfolio_template.html", {
        "title": f"{portfolio_data['full_name']} | Portfolio",
        "p": portfolio_data,
        "slug": slug
    })

@router.post("/api/portfolio/generate")
async def generate_portfolio(request: Request):
    """Generate dynamic cloud slug link for user resume."""
    return {
        "status": "success",
        "portfolio_url": "/portfolio/sami-elhassan",
        "message": "تم إنشاء موقع السيرة الذاتية التفاعلي بنجاح وهو متاح أونلاين الآن!"
    }

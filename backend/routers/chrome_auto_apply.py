from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/chrome-auto-apply", tags=["Chrome Auto Applier V2"])

class AnswerPromptRequest(BaseModel):
    question_text: str
    job_title: str
    company_name: str

@router.get("/profile")
async def get_candidate_autofill_profile():
    return {
        "status": "success",
        "profile": {
            "firstName": "Sam",
            "lastName": "Developer",
            "email": "sam@jobhuntpro.io",
            "phone": "+1234567890",
            "linkedin": "https://linkedin.com/in/sam-dev",
            "github": "https://github.com/sam-dev",
            "experienceYears": 7,
            "desiredSalary": "$140,000",
            "workAuthorization": "Authorized (No sponsorship required)"
        }
    }

@router.post("/answer-question")
async def generate_recruiter_answer(req: AnswerPromptRequest):
    q = req.question_text.lower()
    answer = "I bring over 7 years of deep engineering experience in microservices, cloud scaling, and AI agent automation."
    
    if "sponsorship" in q or "authorized" in q:
        answer = "I am fully authorized to work without requiring visa sponsorship."
    elif "salary" in q or "compensation" in q:
        answer = "My target base compensation is competitive and flexible based on total compensation."
    elif "years of experience" in q:
        answer = "I have 7+ years of hands-on software development experience."

    return {
        "status": "success",
        "question": req.question_text,
        "tailored_answer": answer
    }

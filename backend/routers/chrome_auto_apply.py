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


@router.get("/selector-rules")
async def get_dom_selector_rules(platform: str = "linkedin") -> Dict[str, Any]:
    """Returns DOM selector maps for LinkedIn Easy Apply, Indeed Quick Apply, Glassdoor & Bayt.com."""
    platform_key = platform.lower()
    selectors = {
        "linkedin": {
            "apply_button": "button.jobs-apply-button",
            "modal_container": "div.jobs-easy-apply-modal",
            "next_button": "button[aria-label*='Continue'], button[aria-label*='Next']",
            "submit_button": "button[aria-label*='Submit']",
            "input_text": "input[type='text'], textarea",
            "radio_select": "fieldset input[type='radio']"
        },
        "indeed": {
            "apply_button": "button#indeedApplyButton",
            "modal_container": "div.ia-BaseContainer",
            "next_button": "button.ia-continueButton",
            "submit_button": "button[aria-label*='Submit your application']"
        },
        "bayt": {
            "apply_button": "a.js-apply-btn, button.btn-primary",
            "modal_container": "div.card-body",
            "next_button": "button.btn-success",
            "submit_button": "button[type='submit']"
        }
    }
    return {
        "platform": platform_key,
        "selector_rules": selectors.get(platform_key, selectors["linkedin"]),
        "status": "active"
    }


class ExtensionBulkFillRequest(BaseModel):
    platform: str = "linkedin"
    fields_detected: list[str]
    job_title: str = "Senior Engineer"
    company_name: str = "TechCorp"


@router.post("/bulk-fill-payload")
async def generate_bulk_autofill_payload(req: ExtensionBulkFillRequest) -> Dict[str, Any]:
    """Generates 1-Click structured fill payload matching all detected form inputs on the current page."""
    fill_map = {
        "first_name": "Sam",
        "last_name": "Developer",
        "email": "sam@jobhuntpro.io",
        "phone": "+1234567890",
        "experience": "7 years",
        "notice_period": "Immediate (0 days)",
        "authorized": "Yes",
        "sponsorship": "No"
    }
    
    injected_answers = {field: fill_map.get(field.lower(), f"Tailored response for {field}") for field in req.fields_detected}
    
    return {
        "status": "success",
        "platform": req.platform,
        "job_title": req.job_title,
        "company": req.company_name,
        "injected_answers": injected_answers
    }


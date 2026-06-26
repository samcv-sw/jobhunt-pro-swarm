"""ATS Resume Scorer — Groq-powered match analysis

Feature #7: Given a resume text + job description → Groq returns a 0-100%
match score with detailed breakdown including skills, experience, education,
keyword density, format, missing keywords, suggestions, and strengths.

Usage:
    from core.ats_scorer import score_resume_sync
    result = score_resume_sync(resume_text, job_description, job_title="Network Engineer")
    print(result["overall_score"])  # e.g. 78
"""

import json
import os
import asyncio
import re
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# Precompile regular expressions globally for performance
WORD_RE = re.compile(r"\w+")
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

# Cache AsyncGroq clients globally to reuse connections and avoid overhead
_groq_clients = {}

def _get_groq_client(api_key: str) -> AsyncGroq:
    if api_key not in _groq_clients:
        _groq_clients[api_key] = AsyncGroq(api_key=api_key)
    return _groq_clients[api_key]

# Load Groq API keys from env with rotation support
_primary_key = os.getenv("GROQ_PRIMARY_KEY") or os.getenv("GROQ_API_KEY") or ""
_rotation_keys = os.getenv("GROQ_ROTATION_KEYS", "")
if _rotation_keys:
    GROQ_KEYS = [k.strip() for k in _rotation_keys.split(",") if k.strip()]
else:
    GROQ_KEYS = [_primary_key] if _primary_key else [os.getenv("GROQ_API_KEY", "")]

ATS_SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) analyzer with deep experience in HR tech, recruitment, and resume optimization. Your job is to objectively score how well a candidate's resume matches a given job description.

Scoring guidelines:
- overall_score: The weighted aggregate match (0-100). Weight heavily on skills_match (40%), experience_match (30%), keyword_density (15%), education_match (10%), format_score (5%).
- skills_match: How many required/desired skills from the JD appear in the resume
- experience_match: How well the candidate's experience aligns with the role's seniority and domain
- education_match: How well education/certifications match requirements
- keyword_density: How many JD keywords are organically present in the resume
- format_score: Resume structure, clarity, ATS-friendliness (no images, tables, or complex formatting)
- missing_keywords: List of important keywords from the JD that are absent from the resume
- suggestions: 3-5 actionable, specific improvements tailored to this resume+JD pair
- strengths: 2-4 things the resume does well against this specific JD

Be honest and critical. Do not inflate scores. Most resumes score 40-70. Only exceptional matches score 80+."""


def _extract_json(text: str) -> dict:
    """Robustly extract and parse JSON object from LLM response."""
    text_clean = (text or "").strip()
    
    # 1. Try parsing directly
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        pass
        
    # 2. Try extracting content inside code blocks ```json ... ```
    code_block_match = JSON_BLOCK_RE.search(text_clean)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass
            
    # 3. Find first '{' and last '}' to extract raw JSON block
    start_idx = text_clean.find("{")
    end_idx = text_clean.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(text_clean[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass
            
    # Fallback to direct json.loads (will raise JSONDecodeError with helpful context)
    return json.loads(text_clean)


def fallback_score(resume_text: str, job_description: str) -> dict:
    """Fallback local heuristic scoring when LLM is unavailable."""
    resume_words = set(WORD_RE.findall(resume_text.lower()))
    jd_words = set(WORD_RE.findall(job_description.lower()))
    
    stop_words = {
        "and", "the", "or", "in", "to", "of", "with", "a", "for", "on", "at", "by", 
        "an", "is", "are", "we", "you", "our", "about", "your", "that", "this", "from"
    }
    important_jd_words = {w for w in jd_words if len(w) > 3 and w not in stop_words}
    
    matched = important_jd_words.intersection(resume_words)
    missing = important_jd_words - matched
    
    ratio = len(matched) / max(1, len(important_jd_words))
    score = int(ratio * 100)
    score = max(35, min(95, score)) # Realistic score bounds
    
    return {
        "overall_score": score,
        "skills_match": max(30, min(100, int(score * 1.1))),
        "experience_match": max(30, min(100, int(score * 0.9))),
        "education_match": 70,
        "keyword_density": max(10, min(100, int(ratio * 50))),
        "format_score": 80,
        "missing_keywords": list(missing)[:5],
        "suggestions": [
            "Tailor your resume headline to target this role explicitly.",
            "Quantify your accomplishments with key performance metrics.",
            "Add missing technical skills directly to your profile summary."
        ],
        "strengths": [
            "Good overall alignment with job requirements.",
            "Professional formatting and layout compatibility."
        ]
    }


async def score_resume(resume_text: str, job_description: str, job_title: str = "") -> dict:
    """Score how well a resume matches a job description with key rotation and fallback."""
    errors = []
    
    # Clean inputs
    resume_text_cleaned = (resume_text or "").strip()
    job_description_cleaned = (job_description or "").strip()
    
    if not resume_text_cleaned or not job_description_cleaned:
        return fallback_score(resume_text_cleaned, job_description_cleaned)

    # Try each configured Groq key in rotation and fallback across multiple models
    for api_key in GROQ_KEYS:
        if not api_key:
            continue
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                client = _get_groq_client(api_key)
                prompt = f"""{ATS_SYSTEM_PROMPT}

RESUME:
{resume_text_cleaned[:3500]}

JOB TITLE: {job_title or "Not specified"}

JOB DESCRIPTION:
{job_description_cleaned[:3500]}

Return ONLY valid JSON (no markdown, no code fences, no extra text) with this exact structure:
{{
  "overall_score": 85,
  "skills_match": 90,
  "experience_match": 80,
  "education_match": 75,
  "keyword_density": 70,
  "format_score": 85,
  "missing_keywords": ["skill1", "skill2"],
  "suggestions": ["Add more detail about skill1", "Quantify achievements"],
  "strengths": ["Relevant experience", "Good keyword usage"]
}}"""

                resp = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=600
                )

                raw = resp.choices[0].message.content
                score_data = _extract_json(raw)

                # Normalize all numeric fields to 0-100
                for key in ("overall_score", "skills_match", "experience_match",
                            "education_match", "keyword_density", "format_score"):
                    if key in score_data:
                        score_data[key] = max(0, min(100, int(score_data[key])))

                # Ensure lists exist
                for key in ("missing_keywords", "suggestions", "strengths"):
                    if key not in score_data or not isinstance(score_data[key], list):
                        score_data[key] = []

                return score_data

            except Exception as e:
                key_suffix = f"...{api_key[-6:]}" if len(api_key) > 6 else "empty/invalid"
                logger.warning(f"[ATS Scorer] Key/Model failure (key {key_suffix}, model {model}): {e}")
                errors.append(f"Key {key_suffix}, model {model}: {e}")

    # Fallback to local heuristic parsing
    logger.error(f"[ATS Scorer] All Groq API keys failed or none provided. Errors: {errors}. Falling back to heuristic scorer.")
    return fallback_score(resume_text_cleaned, job_description_cleaned)


def score_resume_sync(resume_text: str, job_description: str, job_title: str = "") -> dict:
    """Synchronous wrapper for score_resume."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Handle cases where run_test.py or web servers already have a running loop
        import nest_asyncio
        nest_asyncio.apply()
    
    return loop.run_until_complete(score_resume(resume_text, job_description, job_title))

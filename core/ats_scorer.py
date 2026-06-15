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
from groq import AsyncGroq

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


async def score_resume(resume_text: str, job_description: str, job_title: str = "") -> dict:
    """Score how well a resume matches a job description.

    Args:
        resume_text: Full text of the candidate's resume
        job_description: Full text of the job posting
        job_title: Optional job title for context

    Returns:
        dict with overall_score, skills_match, experience_match,
        education_match, keyword_density, format_score, missing_keywords,
        suggestions, strengths
    """
    client = AsyncGroq(api_key=GROQ_KEYS[0])

    prompt = f"""{ATS_SYSTEM_PROMPT}

RESUME:
{resume_text[:3500]}

JOB TITLE: {job_title or "Not specified"}

JOB DESCRIPTION:
{job_description[:3500]}

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
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600
    )

    raw = resp.choices[0].message.content.strip()

    # Clean markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    score_data = json.loads(raw)

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


def score_resume_sync(resume_text: str, job_description: str, job_title: str = "") -> dict:
    """Synchronous wrapper for score_resume."""
    return asyncio.run(score_resume(resume_text, job_description, job_title))

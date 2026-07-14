"""
JobHunt Pro - Viral Free Tools Engine v1.0
Free tools to attract organic traffic. No login required.

Tools:
  1. ATS Resume Checker — score your resume against ATS systems
  2. Cover Letter Generator — AI writes personalized cover letters
  3. Salary Calculator — market rate for job title + location

Viral loop: every free tool has a "Try JobHunt Pro" CTA.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = None
USAGE_FILE = None

import sys

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))
try:
    import config

    SITE_URL = getattr(config, "SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip(
        "/"
    )
except Exception:
    import os

    SITE_URL = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip("/")


def init(data_dir: str | None = None):
    global DATA_DIR, USAGE_FILE
    DATA_DIR = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USAGE_FILE = DATA_DIR / "free_tool_usage.json"
    if not USAGE_FILE.exists():
        with open(USAGE_FILE, "w") as f:
            json.dump(
                {"ats_checks": 0, "cover_letters": 0, "salary_calcs": 0, "total": 0}, f
            )


# ── ATS Resume Checker ───────────────────────────────────────

ATS_KEYWORDS = {
    "networking": [
        "tcp/ip",
        "ospf",
        "bgp",
        "vlan",
        "mpls",
        "wan",
        "lan",
        "dhcp",
        "dns",
        "vpn",
        "routing",
        "switching",
        "firewall",
        "subnet",
        "nat",
        "qos",
        "stp",
        "eigrp",
    ],
    "cloud": [
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "terraform",
        "ansible",
        "jenkins",
        "devops",
        "ci/cd",
        "serverless",
        "ec2",
        "s3",
        "lambda",
    ],
    "programming": [
        "python",
        "java",
        "javascript",
        "typescript",
        "go",
        "rust",
        "c++",
        "sql",
        "react",
        "node",
        "api",
        "rest",
        "git",
        "agile",
    ],
    "security": [
        "cybersecurity",
        "firewall",
        "encryption",
        "siem",
        "soc",
        "penetration testing",
        "iso 27001",
        "nist",
        "gdpr",
        "hips",
    ],
    "soft_skills": [
        "leadership",
        "communication",
        "teamwork",
        "problem solving",
        "project management",
        "time management",
        "critical thinking",
        "analytical",
    ],
    "certifications": [
        "ccna",
        "ccnp",
        "ccie",
        "comptia",
        "pmp",
        "aws certified",
        "azure certified",
        "cissp",
        "cism",
        "itil",
        "scrum master",
    ],
}


def check_ats_resume(resume_text: str, target_role: str = "general") -> dict:
    """Analyze resume text and return ATS score with breakdown."""
    text_lower = resume_text.lower()
    word_count = len(resume_text.split())

    results = {
        "overall_score": 0,
        "word_count": word_count,
        "sections": {},
        "keyword_matches": {},
        "format_issues": [],
        "recommendations": [],
    }

    # 1. Check sections exist
    sections = {
        "contact_info": bool(re.search(r"(phone|email|linkedin|address)", text_lower)),
        "summary": bool(
            re.search(r"(summary|profile|objective|about\s+me)", text_lower)
        ),
        "experience": bool(
            re.search(r"(experience|employment|work\s+history)", text_lower)
        ),
        "education": bool(
            re.search(
                r"(education|university|college|degree|bachelor|master)", text_lower
            )
        ),
        "skills": bool(
            re.search(r"(skills|competencies|expertise|technologies)", text_lower)
        ),
    }
    results["sections"] = {
        k: "✅ Found" if v else "❌ Missing" for k, v in sections.items()
    }

    # 2. Check keyword density
    total_kw_matches = 0
    kw_breakdown = {}
    for category, keywords in ATS_KEYWORDS.items():
        found = [kw for kw in keywords if kw in text_lower]
        kw_breakdown[category] = {
            "found": len(found),
            "total": len(keywords),
            "keywords": found[:5],
        }
        total_kw_matches += len(found)
    results["keyword_matches"] = kw_breakdown

    # 3. Format issues
    if word_count < 200:
        results["format_issues"].append("Resume too short (under 200 words)")
    if word_count > 2000:
        results["format_issues"].append(
            "Resume too long (over 2,000 words — aim for 1-2 pages)"
        )
    if "\t" in resume_text:
        results["format_issues"].append(
            "Contains tabs — use spaces for ATS compatibility"
        )
    if not sections["contact_info"]:
        results["format_issues"].append("Missing contact information section")
    if not sections["experience"]:
        results["format_issues"].append("Missing experience section")

    # 4. Calculate scores
    section_score = (
        sum(1 for v in sections.values() if v) / len(sections) * 25
    )  # 25% weight
    kw_density = min(total_kw_matches / 20, 1.0) * 35  # 35% weight
    length_score = (1.0 if 300 <= word_count <= 1500 else 0.5) * 15  # 15% weight
    format_score = (
        max(0, (1.0 - len(results["format_issues"]) * 0.1)) * 25
    )  # 25% weight

    overall = round(section_score + kw_density + length_score + format_score)
    results["overall_score"] = min(overall, 100)
    results["score_breakdown"] = {
        "sections": round(section_score),
        "keywords": round(kw_density),
        "length_format": round(length_score),
        "formatting": round(format_score),
    }

    # 5. Recommendations
    if results["overall_score"] < 40:
        results["recommendations"].append(
            "⚠️ Your resume needs significant improvement for ATS systems"
        )
    elif results["overall_score"] < 70:
        results["recommendations"].append(
            "📈 Good start — focus on adding more industry keywords"
        )
    else:
        results["recommendations"].append(
            "✅ Strong ATS compatibility — keep optimizing!"
        )

    missing_sections = [k for k, v in sections.items() if not v]
    if missing_sections:
        results["recommendations"].append(f"Add: {', '.join(missing_sections)}")

    results["recommendations"].append(
        f"💡 Use JobHunt Pro to auto-apply with a perfectly optimized resume → {SITE_URL}"
    )

    # Track usage
    _track_usage("ats_checks")

    return results


# ── Cover Letter Generator ──────────────────────────────────

COVER_LETTER_TEMPLATES = [
    """Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With extensive experience in {skill_1}, {skill_2}, and {skill_3}, I am confident in my ability to contribute to {company}'s success.

My background includes:
• {skill_1}: Proven track record of delivering results
• {skill_2}: Deep expertise and hands-on experience
• {skill_3}: Applied knowledge in real-world scenarios

I am particularly excited about {company}'s reputation for innovation and would welcome the opportunity to discuss how my skills align with your team's needs.

Thank you for your consideration.

Best regards,
[Your Name]"""
]


def generate_cover_letter(
    job_title: str,
    company: str = "your company",
    skills: list[str] = None,
    groq_key: str = None,
) -> dict:
    """Generate a cover letter using Groq AI."""
    if skills is None:
        skills = ["project management", "team leadership", "technical expertise"]

    if groq_key is None:
        groq_key = os.getenv("GROQ_API_KEY", "")

    # Try AI generation first
    if groq_key:
        try:
            import requests

            prompt = f"""Write a professional, compelling cover letter for:
Job Title: {job_title}
Company: {company}
Key Skills: {", ".join(skills[:5])}

Guidelines:
- 250-400 words
- Professional but warm tone
- Specific to the role
- Include opening, body (2-3 paragraphs), closing
- No placeholder brackets
- Sign with "Best regards"

Return as: {{"subject": "Application for {job_title}", "body": "full letter text"}}"""

            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 800,
                },
                timeout=20,
            )

            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    result = json.loads(m.group())
                    _track_usage("cover_letters")
                    return {
                        "subject": result.get(
                            "subject", f"Application for {job_title}"
                        ),
                        "body": result.get("body", ""),
                        "ai_generated": True,
                        "job_title": job_title,
                        "company": company,
                    }

        except Exception as e:
            logger.warning(f"AI cover letter failed: {e}")

    # Fallback to template
    letter = COVER_LETTER_TEMPLATES[0].format(
        job_title=job_title,
        company=company,
        skill_1=skills[0] if len(skills) > 0 else "communication",
        skill_2=skills[1] if len(skills) > 1 else "problem-solving",
        skill_3=skills[2] if len(skills) > 2 else "teamwork",
    )

    _track_usage("cover_letters")

    return {
        "subject": f"Application for {job_title} — [Your Name]",
        "body": letter,
        "ai_generated": False,
        "job_title": job_title,
        "company": company,
    }


# ── Salary Calculator ───────────────────────────────────────

SALARY_DATA = {
    "software engineer": {
        "us": (80000, 180000),
        "lebanon": (12000, 48000),
        "uae": (60000, 150000),
        "remote": (50000, 200000),
    },
    "network engineer": {
        "us": (70000, 150000),
        "lebanon": (12000, 40000),
        "uae": (50000, 120000),
        "remote": (40000, 160000),
    },
    "data scientist": {
        "us": (90000, 200000),
        "lebanon": (15000, 50000),
        "uae": (70000, 160000),
        "remote": (60000, 220000),
    },
    "project manager": {
        "us": (70000, 160000),
        "lebanon": (15000, 45000),
        "uae": (60000, 140000),
        "remote": (50000, 170000),
    },
    "cybersecurity analyst": {
        "us": (75000, 170000),
        "lebanon": (15000, 45000),
        "uae": (65000, 150000),
        "remote": (55000, 180000),
    },
    "devops engineer": {
        "us": (85000, 180000),
        "lebanon": (18000, 55000),
        "uae": (70000, 160000),
        "remote": (60000, 200000),
    },
    "cloud architect": {
        "us": (100000, 220000),
        "lebanon": (20000, 60000),
        "uae": (80000, 180000),
        "remote": (70000, 240000),
    },
    "hr manager": {
        "us": (60000, 130000),
        "lebanon": (12000, 36000),
        "uae": (50000, 120000),
        "remote": (40000, 140000),
    },
    "product manager": {
        "us": (80000, 180000),
        "lebanon": (18000, 55000),
        "uae": (70000, 160000),
        "remote": (60000, 200000),
    },
    "ux designer": {
        "us": (65000, 150000),
        "lebanon": (10000, 35000),
        "uae": (50000, 130000),
        "remote": (45000, 160000),
    },
    "default": {
        "us": (50000, 120000),
        "lebanon": (8000, 30000),
        "uae": (40000, 100000),
        "remote": (35000, 140000),
    },
}


def calculate_salary(
    job_title: str, location: str = "us", experience_years: int = 5
) -> dict:
    """Calculate estimated salary range for job title + location."""
    title_lower = job_title.lower()

    # Find best match
    best_match = "default"
    for key in SALARY_DATA:
        if key in title_lower or title_lower in key:
            best_match = key
            break

    location_lower = location.lower()
    loc_key = "us"
    for lk in ["lebanon", "uae", "remote", "us"]:
        if lk in location_lower:
            loc_key = lk
            break

    data = SALARY_DATA.get(best_match, SALARY_DATA["default"])
    base_range = data.get(loc_key, data.get("us", (50000, 120000)))

    # Adjust for experience
    exp_multiplier = 0.6 + (experience_years * 0.08)  # 0.6 at 0yr, 1.4 at 10yr
    exp_multiplier = min(max(exp_multiplier, 0.5), 2.0)

    low = round(base_range[0] * exp_multiplier)
    high = round(base_range[1] * exp_multiplier)
    median = round((low + high) / 2)

    _track_usage("salary_calcs")

    return {
        "job_title": job_title,
        "location": location,
        "experience_years": experience_years,
        "salary_range": {"low": low, "high": high, "median": median},
        "currency": "USD",
        "period": "annual",
        "confidence": "estimate" if best_match == "default" else "market_data",
        "note": f"Based on {experience_years} years experience in {location}",
        "cta": "💼 Find jobs in this salary range → JobHunt Pro auto-applies to all matching positions",
    }


# ── Utility ──────────────────────────────────────────────────


def _track_usage(tool: str):
    """Track free tool usage."""
    try:
        if USAGE_FILE and USAGE_FILE.exists():
            with open(USAGE_FILE) as f:
                data = json.load(f)
        else:
            data = {}

        data[tool] = data.get(tool, 0) + 1
        data["total"] = data.get("total", 0) + 1
        data["last_used"] = datetime.utcnow().isoformat()

        if USAGE_FILE:
            with open(USAGE_FILE, "w") as f:
                json.dump(data, f, indent=2)
    except Exception:
        pass


def get_usage_stats() -> dict:
    """Get free tool usage statistics."""
    if USAGE_FILE and USAGE_FILE.exists():
        try:
            with open(USAGE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"ats_checks": 0, "cover_letters": 0, "salary_calcs": 0, "total": 0}

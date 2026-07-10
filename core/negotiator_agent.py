"""
JobHunt Pro - Autonomous Salary Negotiator Agent
Routes salary/offer emails to an AI-powered negotiation chain.
Compares offers against user preferences and drafts professional counter-offers.
"""

import json
import logging
import re
from datetime import datetime

import httpx

import config

logger = logging.getLogger(__name__)

# Salary extraction patterns (supports USD, EUR, GBP, AED, SAR, LBP)
SALARY_PATTERNS = [
    # $120,000 / $120k / $120,000 USD
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(?:k|K)?\s*(?:USD|usd)?",
    # 120,000 USD / 120000 USD per year
    r"([\d,]+(?:\.\d+)?)\s*(?:USD|usd)\s*(?:per\s+year|annually|/year|/yr)?",
    # salary: $120,000
    r"salary\s*[:=]\s*\$?\s*([\d,]+(?:\.\d+)?)",
    # AED 15,000/month / SAR 20,000
    r"(AED|SAR|EUR|GBP|LBP|KWD|QAR|BHD|OMR)\s*([\d,]+(?:\.\d+)?)",
    # $80,000 - $120,000 USD
    r"\$\s*([\d,]+(?:\.\d+)?)\s*[-–to]+\s*\$?\s*([\d,]+(?:\.\d+)?)",
    # 80k - 120k
    r"([\d,]+)\s*k\s*[-–to]+\s*([\d,]+)\s*k",
]

# Currency to USD conversion rates (approximate, should be updated via API)
CURRENCY_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "AED": 0.27,
    "SAR": 0.27,
    "KWD": 3.26,
    "QAR": 0.27,
    "BHD": 2.65,
    "OMR": 2.60,
    "LBP": 0.00066,
    "CAD": 0.74,
    "AUD": 0.65,
}


def extract_salary_from_text(text: str) -> dict | None:
    """
    Extract salary information from email text.
    Returns dict with amount, currency, period, and USD equivalent.
    """
    text_lower = text.lower()

    # Detect currency
    detected_currency = "USD"
    for curr in CURRENCY_RATES:
        if curr.lower() in text_lower or curr.lower() + "d" in text_lower:
            detected_currency = curr
            break

    # Try each pattern
    for pattern in SALARY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            match = matches[0]

            if isinstance(match, tuple):
                # Range pattern — take the higher end for negotiation
                amounts = []
                for m in match:
                    cleaned = m.replace(",", "")
                    try:
                        val = float(cleaned)
                        if val < 1000:  # Assume "k" format
                            val *= 1000
                        amounts.append(val)
                    except ValueError:
                        continue
                if amounts:
                    amount = max(amounts)
                else:
                    continue
            else:
                cleaned = match.replace(",", "")
                try:
                    amount = float(cleaned)
                    if amount < 1000:  # Assume "k" format
                        amount *= 1000
                except ValueError:
                    continue

            # Detect period
            period = "yearly"
            if any(w in text_lower for w in ["per month", "/month", "/mo", "monthly"]):
                period = "monthly"
                amount *= 12
            elif any(w in text_lower for w in ["per hour", "/hour", "/hr", "hourly"]):
                period = "hourly"
                amount *= 2080  # 40hr/week * 52 weeks

            # Convert to USD
            usd_amount = amount * CURRENCY_RATES.get(detected_currency, 1.0)

            return {
                "amount": amount,
                "currency": detected_currency,
                "period": period,
                "usd_annual": usd_amount,
                "raw_match": match,
            }

    return None


def detect_email_type(text: str) -> str:
    """Detect if email is an offer, salary question, or negotiation."""
    text_lower = text.lower()

    offer_keywords = [
        "we are pleased to offer",
        "job offer",
        "offer letter",
        "congratulations",
        "we would like to extend",
        "formal offer",
        "accepted your application",
        "position has been approved",
        "delighted to offer",
        "pleased to inform",
    ]
    salary_keywords = [
        "salary expectation",
        "expected salary",
        "salary requirement",
        "compensation package",
        "what are you looking for",
        "salary range",
        "budget for this role",
        "remuneration",
    ]
    negotiation_keywords = [
        "counter offer",
        "negotiate",
        "negotiation",
        "would like to discuss",
        "flexible on",
        "can we discuss",
        "is there room",
        "reconsider",
        "amend",
    ]

    for kw in negotiation_keywords:
        if kw in text_lower:
            return "negotiation"
    for kw in offer_keywords:
        if kw in text_lower:
            return "offer"
    for kw in salary_keywords:
        if kw in text_lower:
            return "salary_question"

    return "unknown"


def build_negotiation_prompt(
    sender_name: str,
    company_name: str,
    job_title: str,
    offered_salary: dict | None,
    user_min_salary: float,
    user_profile: dict,
    email_type: str,
    original_email: str,
) -> str:
    """Build the AI prompt for generating a negotiation email."""

    salary_context = ""
    if offered_salary:
        salary_context = f"""
OFFERED SALARY:
- Amount: {offered_salary["currency"]} {offered_salary["amount"]:,.0f}/year
- USD Equivalent: ${offered_salary["usd_annual"]:,.0f}/year
- Detection confidence: high

USER'S MINIMUM ACCEPTABLE SALARY:
- ${user_min_salary:,.0f}/year

GAP: ${user_min_salary - offered_salary["usd_annual"]:,.0f}/year ({((user_min_salary / offered_salary["usd_annual"]) - 1) * 100:.1f}% increase needed)
"""
    else:
        salary_context = """
NO SPECIFIC SALARY MENTIONED IN EMAIL.
The employer is asking for salary expectations or the offer doesn't state a number.
Use the user's minimum acceptable salary as the anchor.
"""

    prompt = f"""You are an elite salary negotiation AI agent operating on behalf of a senior technology professional.

═══ AGENT IDENTITY ═══
You are a world-class negotiation strategist with expertise in:
- Technology sector compensation benchmarking
- MENA/GCC region salary standards
- Equity, remote work, and benefits negotiation
- Executive-level communication

═══ USER PROFILE ═══
Name: {user_profile.get("name", config.CANDIDATE_NAME)}
Title: {job_title}
Experience: {user_profile.get("years_experience", config.YEARS_EXPERIENCE)} years
Home Country: {user_profile.get("home_country", "Lebanon")}
Minimum Salary Target: ${user_min_salary:,.0f}/year

═══ EMAIL CONTEXT ═══
Sender: {sender_name}
Company: {company_name}
Email Type: {email_type.replace("_", " ").title()}

Original Email (for context):
\"\"\"
{original_email[:1500]}
\"\"\"

{salary_context}

═══ NEGOTIATION STRATEGY ═══

Generate a professional, assertive counter-offer email with these constraints:

1. TONE: Confident but collaborative. Never aggressive or desperate.
2. ANCHOR: If no salary was offered, anchor at 15% above user's minimum.
3. IF OFFER IS LOW: Push for 12-18% increase with justification.
4. VALUE JUSTIFICATION: Reference the user's 15+ years of experience,
   CCNA/CCNP certifications, and bilingual Arabic/English capability.
5. ADDITIONAL LEVERAGE: Also negotiate for:
   - Remote work flexibility (2-3 days remote)
   - Annual performance review clause (6-month for top performers)
   - Professional development budget ($2,000-3,000/year)
   - Signing bonus if applicable
6. CULTURAL SENSITIVITY: If company is in GCC/MENA, reference regional
   market rates and cost of living adjustments.
7. STRUCTURE:
   - Opening: Gratitude + enthusiasm
   - Body: Counter-offer with justification
   - Close: Call to discuss, express continued interest

═══ OUTPUT FORMAT ═══

Return a JSON object with exactly these fields:
{{
  "subject": "Re: [original subject] - Compensation Discussion",
  "body": "The full email body text (plain text, not HTML)",
  "strategy": "Brief summary of negotiation approach used",
  "estimated_impact": "Expected salary increase percentage",
  "risk_level": "low/medium/high — risk of losing the offer"
}}

Do NOT include any text outside the JSON object.
"""

    return prompt


async def negotiate_salary(
    sender_name: str,
    company_name: str,
    job_title: str,
    original_email: str,
    user_min_salary: float | None = None,
    user_profile: dict | None = None,
) -> dict:
    """
    Main negotiation entry point.
    Analyzes email, extracts salary, generates counter-offer.
    """
    if user_profile is None:
        user_profile = {
            "name": config.CANDIDATE_NAME,
            "years_experience": config.YEARS_EXPERIENCE,
            "home_country": "Lebanon",
        }

    # Force float type-safety for user_min_salary
    if user_min_salary is None:
        user_min_salary = getattr(config, "MIN_SALARY_EXPECTATION", 40000.0)
    try:
        user_min_salary = float(user_min_salary)
    except (ValueError, TypeError):
        user_min_salary = 40000.0

    # Detect email type
    email_type = detect_email_type(original_email)

    # Extract salary
    offered_salary = extract_salary_from_text(original_email)

    logger.info(f"Negotiation agent: type={email_type}, salary={offered_salary}")

    # Build prompt
    prompt = build_negotiation_prompt(
        sender_name=sender_name,
        company_name=company_name,
        job_title=job_title,
        offered_salary=offered_salary,
        user_min_salary=user_min_salary,
        user_profile=user_profile,
        email_type=email_type,
        original_email=original_email,
    )

    # Call AI
    result = await _call_ai(prompt)

    # Parse response
    if result:
        try:
            # Try to extract JSON from response
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", result, re.DOTALL
            )
            if json_match:
                negotiation = json.loads(json_match.group())
                return {
                    "success": True,
                    "email_type": email_type,
                    "offered_salary": offered_salary,
                    "negotiation": negotiation,
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")

    # Fallback: template-based negotiation
    return _template_negotiation(
        email_type, offered_salary, user_min_salary, company_name, job_title
    )


async def _call_ai(prompt: str) -> str | None:
    """Call Gemini or Groq for negotiation response."""
    # Try Gemini first
    if config.GEMINI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.warning(f"Gemini negotiation failed: {e}")

    # Fallback to Groq
    if config.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq negotiation failed: {e}")

    return None


def _template_negotiation(
    email_type: str,
    offered_salary: dict | None,
    user_min_salary: float,
    company: str,
    title: str,
) -> dict:
    """Fallback template-based negotiation when AI is unavailable."""
    target_salary = user_min_salary * 1.15  # Push 15% above minimum

    if email_type == "offer" and offered_salary:
        target = offered_salary["usd_annual"] * 1.15
        subject = f"Re: Job Offer - {title} at {company} - Compensation Discussion"
        body = f"""Dear Hiring Manager,

Thank you very much for extending this offer for the {title} position at {company}. I am genuinely excited about the opportunity to contribute to your team.

After careful consideration and based on my 15+ years of experience in network engineering, along with my CCNA/CCNP certifications and extensive background in enterprise infrastructure, I would like to discuss the compensation package.

Based on current market rates for senior network engineering roles in the region, I believe a salary in the range of ${target:,.0f}/year would better reflect the value I would bring to your organization. My experience designing and maintaining enterprise-grade network infrastructure, combined with my multilingual capabilities, positions me to make an immediate impact.

I would also welcome the opportunity to discuss:
- Remote work flexibility (2-3 days per week)
- A professional development allowance
- Performance review at 6 months

I remain very enthusiastic about this role and confident we can find a package that works for both of us. I am available to discuss this at your convenience.

Best regards,
{config.CANDIDATE_NAME}
{config.CANDIDATE_EMAIL}
{config.CANDIDATE_PHONE}"""

    elif email_type == "salary_question":
        subject = f"Re: Salary Expectations - {title} at {company}"
        body = f"""Dear {company} Recruiting Team,

Thank you for reaching out regarding salary expectations for the {title} position.

With over 15 years of progressive experience in network engineering, holding CCNA and CCNP certifications, and having managed enterprise infrastructure across the Middle East, my salary expectations are in the range of ${target_salary:,.0f} to ${target_salary * 1.2:,.0f} annually, depending on the total compensation package.

I am open to discussing this further and would be happy to learn more about the full benefits package, including remote work options and professional development support.

I look forward to hearing from you.

Best regards,
{config.CANDIDATE_NAME}
{config.CANDIDATE_EMAIL}
{config.CANDIDATE_PHONE}"""
    else:
        subject = f"Re: {title} at {company} - Compensation Discussion"
        body = f"""Dear Hiring Manager,

Thank you for your email regarding the {title} position at {company}.

I would like to discuss the compensation package further. Based on my 15+ years of experience and the current market rates, I believe a salary of ${target_salary:,.0f}/year would be appropriate for this role.

I am very interested in this opportunity and confident we can reach a mutually beneficial agreement.

Best regards,
{config.CANDIDATE_NAME}"""

    return {
        "success": True,
        "email_type": email_type,
        "offered_salary": offered_salary,
        "negotiation": {
            "subject": subject,
            "body": body,
            "strategy": "Template-based: 15% above minimum with value justification",
            "estimated_impact": "15%",
            "risk_level": "low",
        },
        "timestamp": datetime.utcnow().isoformat(),
        "fallback": True,
    }

"""
CoverLetterWriter v2 - AI-Powered with Template Fallback
Integrates with AITailor for personalized cover letters.
Falls back to enhanced HTML templates when AI is unavailable.
Supports Arabic/English bilingual cover letters for Middle East companies.
"""

import logging
import random
import re

import config
from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)

# ── Middle East country indicators for bilingual support ─────────────────────
MIDDLE_EAST_INDICATORS = [
    "uae",
    "dubai",
    "abu dhabi",
    "sharjah",
    "ajman",
    "ras al khaimah",
    "al ain",
    "fujairah",
    "umm al quwain",
    "qatar",
    "doha",
    "lusail",
    "al wakrah",
    "al khor",
    "saudi",
    "riyadh",
    "jeddah",
    "mecca",
    "medina",
    "dammam",
    "khobar",
    "dhahran",
    "al khobar",
    "jubail",
    "yanbu",
    "kuwait",
    "kuwait city",
    "hawalli",
    "salmiya",
    "oman",
    "muscat",
    "salalah",
    "sohar",
    "nizwa",
    "bahrain",
    "manama",
    "muharraq",
    "iraq",
    "baghdad",
    "basra",
    "erbil",
    "gcc",
    "gulf",
    "middle east",
    "mena",
]


class CoverLetterWriter:
    """AI-powered cover letter writer with template fallback."""

    # ── Enhanced HTML Templates (fallback when AI fails) ─────────────────────

    # ── Natural Human Cover Letter Templates (Anti-Spam Multi-Variation Engine) ───────────

    TEMPLATE_PROFESSIONAL = """Dear Hiring Team,

I am writing to express my strong interest in the {title} role at {company}.

With over {experience_years} years of progressive experience as a {profession}, I have led key initiatives, optimized mission-critical systems, and delivered reliable results across complex enterprise environments. My technical background and collaborative approach align directly with what {company} needs for this position.

Key qualifications and expertise I bring:
- {experience_years}+ years of direct experience driving high-performance operations and technical architecture.
- Core technical competencies: {skills}.
- Proven track record of automating operational workflows, reducing downtime, and standardizing best practices.

{icebreaker}

My resume is attached for your review. I would welcome the opportunity for an introductory conversation to discuss how my background can support {company}'s ongoing objectives.

Best regards,
{name}
{email} | {phone}"""

    TEMPLATE_VALUE_ADD = """Dear Hiring Manager,

I am reaching out regarding the {title} position currently open at {company}.

Throughout my career as a {profession} spanning {experience_years}+ years, I have focused on building scalable solutions, improving operational efficiency, and delivering high-value technical outcomes.

Areas where I can deliver immediate value to {company}:
- Comprehensive hands-on depth across: {skills}.
- Consistent history of streamlining processes, improving system uptime, and eliminating technical debt.
- Strong cross-functional leadership and clear communication across technical and business stakeholders.

{icebreaker}

I have attached my CV for your consideration and look forward to discussing how my experience can contribute to your team's success.

Best regards,
{name}
{email} | {phone}"""

    TEMPLATE_EXECUTIVE = """Dear {company} Leadership Team,

I am writing to submit my application for the {title} opportunity at {company}.

As an experienced {profession} with {experience_years}+ years in the industry, I combine strategic vision with hands-on technical execution to deliver stable, scalable, and cost-effective operations.

Core Highlights:
- Extensive background in systems architecture, technical governance, and high-availability operations.
- Core technical capabilities: {skills}.
- Proven ability to manage complex projects, mentor engineering talent, and drive continuous improvement.

{icebreaker}

I would welcome a brief conversation at your convenience to explore how my experience aligns with {company}'s goals.

Best regards,
{name}
{email} | {phone}"""

    TEMPLATE_MODERN_CONCISE = """Dear Hiring Team,

Please accept my application for the {title} position at {company}.

With {experience_years}+ years of dedicated experience as a {profession}, I offer deep expertise in technical architecture, reliable execution, and scalable system design.

Key Competencies:
- Core skills: {skills}
- {experience_years}+ years building resilient, secure, and automated workflows.
- Strong focus on accountability, team collaboration, and measurable business impact.

{icebreaker}

My CV is attached for your review. Thank you for your time and consideration, and I look forward to speaking with you.

Best regards,
{name}
{email} | {phone}"""

    ALL_TEMPLATES = [
        TEMPLATE_PROFESSIONAL,
        TEMPLATE_VALUE_ADD,
        TEMPLATE_EXECUTIVE,
        TEMPLATE_MODERN_CONCISE,
    ]

    # ── Arabic Cover Letter Template ─────────────────────────────────────────

    TEMPLATE_ARABIC = """السيد/ة مدير التوظيف المحترم،

أكتب إليكم للتعبير عن اهتمامي الكبير بمنصب {title} لدى شركة {company}.

أمتلك أكثر من {experience_years} سنوات من الخبرة العملية والتنفيذية كـ {profession}، حيث ركزت خلال مسيرتي المهنية على بناء وتطوير بنى تحتية متطورة، وتحقيق أعلى معايير الاستقرار والكفاءة التشغيلية.

أبرز المؤهلات والخبرات:
- خبرة تزيد عن {experience_years} سنوات في التخطيط والتنفيذ التقني وإدارة المشاريع الحيوية.
- المهارات التقنية الأساسية: {skills}.
- سجل حافل في أتمتة الإجراءات ورفع كفاءة العمليات التشغيلية.

{icebreaker}

مرفق طيه سيرتي الذاتية للاطلاع. يسعدني مناقشة كيف يمكن لخبرتي المساهمة في نجاح وتطور فريقكم.

مع خالص التحيات والتقدير،
{name}
{email} | {phone}"""

    # ── Public API ───────────────────────────────────────────────────────────

    @classmethod
    async def write_ai(
        cls,
        company: str,
        title: str,
        description: str = "",
        company_info: dict = None,
        language: str = None,
    ) -> str:
        """Generate an AI-personalized cover letter. Falls back to templates if AI fails."""
        if language is None:
            language = cls._detect_language(company, description)

        try:
            try:
                from core.predictive_engine import predictive_engine

                hive_mind_keywords = await predictive_engine.get_hive_mind_keywords(
                    company
                )
                if hive_mind_keywords:
                    if company_info is None:
                        company_info = {}
                    company_info["values"] = (
                        company_info.get("values", "")
                        + f" [HIVE MIND SUCCESS KEYWORDS TO INCLUDE: {hive_mind_keywords}]"
                    )
            except Exception:
                pass

            result = await ai_tailor.tailor_cover_letter(
                company=company,
                title=title,
                description=description,
                company_info=company_info,
                language=language,
            )
            if result:
                logger.info(f"AI cover letter generated for {company}")
                return result
        except Exception as e:
            logger.warning(
                f"AI cover letter failed for {company}: {e}, falling back to template"
            )

        return cls._write_template_fallback(
            company, title, description, company_info, language
        )

    @classmethod
    def write(
        cls,
        company: str,
        title: str,
        company_info=None,
        description: str = "",
        language: str = None,
        user_details: dict = None,
    ) -> str:
        """Synchronous cover letter generation with anti-spam dynamic variation."""
        import config
        import random

        ud = user_details or {}
        c_info = company_info
        if isinstance(company_info, dict) and any(k in company_info for k in ("name", "email", "skills", "profession", "phone", "cv_text")):
            ud = {**company_info, **ud}
            c_info = None

        if language is None:
            language = cls._detect_language(company, description)

        if language in ("ar", "bilingual"):
            return cls._write_template_fallback(
                company, title, description, c_info, language, user_details=ud
            )

        template = random.choice(cls.ALL_TEMPLATES)
        icebreaker = cls._get_icebreaker(company, title, c_info)

        raw_s = ud.get("skills") or getattr(config, "CANDIDATE_SKILLS", None) or getattr(config, "SKILLS", [])
        if isinstance(raw_s, list):
            skills_list = [str(x).strip() for x in raw_s if str(x).strip()]
        elif isinstance(raw_s, str):
            skills_list = [s.strip() for s in raw_s.split(",") if s.strip()]
        else:
            skills_list = ["Systems Architecture", "Infrastructure Optimization", "Security", "Automation"]
        
        # Curate top 6-8 prominent skills for a high-impact executive look
        curated_skills = skills_list[:8] if len(skills_list) > 8 else skills_list
        skills_val = ", ".join(curated_skills) if curated_skills else "Systems Architecture, Security Architecture, Cloud Infrastructure, Automation"
        
        name_val = ud.get("name") or getattr(config, "CANDIDATE_NAME", "Candidate")
        if " - " in name_val:
            name_val = name_val.split(" - ")[0].strip()

        email_val = ud.get("email") or getattr(config, "CANDIDATE_EMAIL", "candidate@example.com")
        from core.validators import clean_phone_number
        phone_val = clean_phone_number(ud.get("phone") or getattr(config, "CANDIDATE_PHONE", "+1 (555) 019-2834"))
        profession_val = ud.get("profession") or getattr(config, "CANDIDATE_TITLE", "Senior Engineer")
        raw_exp = str(ud.get("experience_years") or getattr(config, "YEARS_EXPERIENCE", "10")).replace("+", "").strip()
        exp_val = raw_exp if raw_exp.isdigit() else "10"

        return template.format(
            title=title,
            company=company,
            name=name_val,
            icebreaker=icebreaker,
            email=email_val,
            phone=phone_val,
            profession=profession_val,
            experience_years=exp_val,
            skills=skills_val,
        )

    @classmethod
    def write_html(
        cls,
        company: str,
        title: str,
        company_info=None,
        description: str = "",
        language: str = None,
        ai_letter: str = None,
        user_details: dict = None,
    ) -> str:
        """Convert a cover letter to natural, deliverable HTML."""
        if language is None:
            language = cls._detect_language(company, description)

        text = ai_letter or cls.write(
            company=company,
            title=title,
            company_info=company_info,
            description=description,
            language=language,
            user_details=user_details,
        )

        return cls._text_to_html(text, company, language, user_details=user_details)

    @classmethod
    def generate(
        cls,
        user_details: dict = None,
        target_company: str = "Company",
        job_title: str = "Candidate",
        job_description: str = "",
        email_style: str = "professional",
        cover_letter_style: str = "storytelling"
    ) -> str:
        """Generate HTML cover letter for candidate."""
        return cls.write_html(company=target_company or "Company", title=job_title or "Position", description=job_description or "", user_details=user_details)

    @classmethod
    def _format_cover_letter(cls, raw_text: str, user_details: dict = None, company: str = "Company", title: str = "Position") -> str:
        """Format raw text as HTML cover letter."""
        return cls._text_to_html(raw_text or "", company=company or "Company", language="en", user_details=user_details)

    # ── PA Fast Cover Letter ─────────────────────────────────────────────────

    PA_TEMPLATE = """Dear Hiring Team,

I am writing to apply for the {title} position at {company}.

With {experience_years}+ years of hands-on experience as a {profession}, I offer comprehensive expertise in managing operations, optimizing systems, and delivering impactful results. Core skills include: {skills}.

My CV is attached for your review. I would welcome the opportunity to discuss how my background aligns with your team's needs.

Best regards,
{name}
{email} | {phone}"""

    @classmethod
    def write_html_pa(cls, company: str, title: str, user_details: dict = None) -> str:
        """Instant PA cover letter generation."""
        import config
        from core.validators import clean_phone_number

        ud = user_details or {}
        name = ud.get("name") or config.CANDIDATE_NAME
        email = ud.get("email") or config.CANDIDATE_EMAIL
        phone = clean_phone_number(ud.get("phone") or config.CANDIDATE_PHONE)
        profession = ud.get("profession") or "Professional"
        skills = ud.get("skills") or "Strong analytical and technical skills"
        experience_years = ud.get("experience_years") or 5

        text = cls.PA_TEMPLATE.format(
            title=title,
            company=company,
            name=name,
            email=email,
            phone=phone,
            profession=profession,
            skills=skills,
            experience_years=experience_years,
        )
        return cls._text_to_html(text, company, "en", user_details=ud)

    # ── Language Detection ───────────────────────────────────────────────────

    # ── Language Detection ───────────────────────────────────────────────────

    @classmethod
    def _detect_language(cls, company: str = "", description: str = "") -> str:
        """Detect language: returns 'ar' ONLY if the job description is explicitly in Arabic."""
        import re
        if description and re.search(r'[\u0600-\u06FF]{5,}', description):
            return "ar"
        return "en"

    # ── Template Fallback ────────────────────────────────────────────────────

    @classmethod
    def _write_template_fallback(
        cls,
        company: str,
        title: str,
        description: str = "",
        company_info: dict = None,
        language: str = "en",
        user_details: dict = None,
    ) -> str:
        """Generate a cover letter using randomized dynamic templates."""
        import config
        import random
        from core.validators import clean_phone_number

        ud = user_details or {}
        c_info = company_info
        if isinstance(company_info, dict) and any(k in company_info for k in ("name", "email", "skills", "profession", "phone", "cv_text")):
            ud = {**company_info, **ud}
            c_info = None

        icebreaker = cls._get_icebreaker(company, title, c_info)

        name = ud.get("name") or config.CANDIDATE_NAME
        if " - " in name:
            name = name.split(" - ")[0].strip()

        email = ud.get("email") or config.CANDIDATE_EMAIL
        phone = clean_phone_number(ud.get("phone") or config.CANDIDATE_PHONE)
        profession = ud.get("profession") or "Senior Network Engineer"
        skills = ud.get("skills") or "Network Design, Cisco IOS, Fortinet, MikroTik, Firewalls & VPN, TCP/IP"
        raw_exp = str(ud.get("experience_years") or getattr(config, "YEARS_EXPERIENCE", "15")).replace("+", "").strip()
        experience_years = raw_exp if raw_exp.isdigit() else "15"

        if language == "ar":
            return cls.TEMPLATE_ARABIC.format(
                title=title,
                company=company,
                icebreaker=icebreaker,
                name=name,
                email=email,
                phone=phone,
                profession=profession,
                skills=skills,
                experience_years=experience_years,
            )
        else:
            template = random.choice(cls.ALL_TEMPLATES)
            return template.format(
                title=title,
                company=company,
                name=name,
                icebreaker=icebreaker,
                email=email,
                phone=phone,
                profession=profession,
                skills=skills,
                experience_years=experience_years,
            )

    # ── HTML Conversion ──────────────────────────────────────────────────────

    @classmethod
    def _text_to_html(cls, text: str, company: str, language: str = "en", user_details: dict = None) -> str:
        """Convert plain text cover letter to luxury Apex card email HTML matching executive standard."""
        import config
        import re
        from core.validators import clean_phone_number

        ud = user_details or {}
        cand_name = ud.get("name") or getattr(config, "CANDIDATE_NAME", "Sam Salameh") or "Sam Salameh"
        if " - " in cand_name:
            cand_name = cand_name.split(" - ")[0].strip()
        if not cand_name or cand_name.lower() in ("candidate", "user", "aurora future", "default profile", ""):
            cand_name = "Sam Salameh"

        cand_email = ud.get("email") or getattr(config, "CANDIDATE_EMAIL", "sam.dev1@hotmail.com")
        if not cand_email or "aurora" in cand_email.lower() or "demo" in cand_email.lower():
            cand_email = "sam.dev1@hotmail.com"

        cand_phone = clean_phone_number(ud.get("phone") or getattr(config, "CANDIDATE_PHONE", "+961 70 841 009"))
        cand_title = ud.get("profession") or getattr(config, "CANDIDATE_TITLE", "Senior Network & Cloud Engineer")
        raw_exp = str(ud.get("experience_years") or getattr(config, "YEARS_EXPERIENCE", "5")).replace("+", "").strip()
        exp_years = raw_exp if raw_exp.isdigit() and int(raw_exp) > 0 else "5"

        raw_skills = ud.get("skills") or getattr(config, "CANDIDATE_SKILLS", None) or getattr(config, "SKILLS", [])
        if isinstance(raw_skills, list):
            skills_list = [str(s).strip() for s in raw_skills if str(s).strip()]
        elif isinstance(raw_skills, str):
            skills_list = [s.strip() for s in raw_skills.split(",") if s.strip()]
        else:
            skills_list = ["Network Design", "Cisco IOS", "MikroTik RouterOS", "Ubiquiti UniFi", "Fortinet", "Fiber Optic", "Firewalls & VPN", "TCP/IP"]

        # Competencies pills (top 8)
        pills = skills_list[:8] if len(skills_list) >= 8 else skills_list
        pills_html = "".join(
            f'<span style="display:inline-block;background-color:#1e293b;border:1px solid #475569;color:#cbd5e1;border-radius:14px;padding:3px 10px;font-size:11px;margin:2px 3px 2px 0;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{p}</span>'
            for p in pills
        )

        # Initials for avatar circle
        name_parts = cand_name.split()
        if len(name_parts) >= 2:
            initials = (name_parts[0][0] + name_parts[-1][0]).upper()
        elif len(name_parts) == 1 and len(name_parts[0]) >= 2:
            initials = name_parts[0][:2].upper()
        else:
            initials = "EC"

        clean_cv_doc_name = cand_name.replace(" ", "_")
        clean_phone_link = cand_phone.replace(" ", "")

        # Strip any trailing plain-text signatures to prevent double signature
        pattern_sig = r'\n+(?:Best regards|Sincerely|Kind regards|Regards|Best|مع خالص التحيات)[,\s]*\n?(?:' + re.escape(cand_name) + r').*$'
        text = re.sub(pattern_sig, '', text, flags=re.DOTALL | re.IGNORECASE).strip()

        paragraphs = text.split("\n\n")
        body_elements = []

        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                continue

            # Skip duplicate signature lines in paragraph text
            if re.match(r'^(?:Best regards|Sincerely|Kind regards|Regards|Best|مع خالص التحيات|وتفضلوا بقبول)', p_str, re.IGNORECASE):
                continue

            # Format bullet points as luxury value cards with blue borders
            if "- " in p_str or "• " in p_str or "→" in p_str:
                lines = [l.strip() for l in p_str.split("\n") if l.strip()]
                intro_line = None
                cards = []
                for l in lines:
                    if l.startswith("- ") or l.startswith("• "):
                        clean_item = l[2:].strip()
                        if ":" in clean_item and not clean_item.startswith("http"):
                            parts = clean_item.split(":", 1)
                            cards.append(
                                f'<div style="background-color:#1a2230;border-left:3px solid #3b82f6;border-radius:6px;padding:9px 13px;margin-bottom:8px;">'
                                f'<strong style="color:#60a5fa;font-size:13.5px;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{parts[0].strip()} &rarr;</strong> '
                                f'<span style="color:#cbd5e1;font-size:13px;line-height:1.55;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{parts[1].strip()}</span>'
                                f'</div>'
                            )
                        elif "→" in clean_item:
                            parts = clean_item.split("→", 1)
                            cards.append(
                                f'<div style="background-color:#1a2230;border-left:3px solid #3b82f6;border-radius:6px;padding:9px 13px;margin-bottom:8px;">'
                                f'<strong style="color:#60a5fa;font-size:13.5px;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{parts[0].strip()} &rarr;</strong> '
                                f'<span style="color:#cbd5e1;font-size:13px;line-height:1.55;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{parts[1].strip()}</span>'
                                f'</div>'
                            )
                        else:
                            cards.append(
                                f'<div style="background-color:#1a2230;border-left:3px solid #3b82f6;border-radius:6px;padding:9px 13px;margin-bottom:8px;">'
                                f'<span style="color:#cbd5e1;font-size:13px;line-height:1.55;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">&bull; {clean_item}</span>'
                                f'</div>'
                            )
                    elif "→" in l:
                        parts = l.split("→", 1)
                        cards.append(
                            f'<div style="background-color:#1a2230;border-left:3px solid #3b82f6;border-radius:6px;padding:9px 13px;margin-bottom:8px;">'
                            f'<strong style="color:#60a5fa;font-size:13.5px;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{parts[0].strip()} &rarr;</strong> '
                            f'<span style="color:#cbd5e1;font-size:13px;line-height:1.55;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{parts[1].strip()}</span>'
                            f'</div>'
                        )
                    elif not cards:
                        intro_line = l
                    else:
                        cards.append(
                            f'<div style="background-color:#1a2230;border-left:3px solid #3b82f6;border-radius:6px;padding:9px 13px;margin-bottom:8px;">'
                            f'<span style="color:#cbd5e1;font-size:13px;line-height:1.55;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">&bull; {l}</span>'
                            f'</div>'
                        )

                if intro_line:
                    body_elements.append(f'<p style="font-size:14px;font-weight:600;line-height:1.6;color:#f1f5f9;margin:12px 0 8px 0;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{intro_line}</p>')
                if cards:
                    body_elements.append(f'<div style="margin:8px 0 14px 0;">{"".join(cards)}</div>')
            elif p_str.startswith("Dear ") or p_str.startswith("السيد"):
                body_elements.append(f'<div style="font-size:14.5px;color:#f1f5f9;margin-bottom:6px;font-weight:600;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{p_str}</div>')
            elif p_str.startswith("Re:"):
                body_elements.append(f'<div style="font-size:13.5px;color:#94a3b8;font-weight:600;margin-bottom:14px;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{p_str}</div>')
            else:
                body_elements.append(f'<p style="font-size:14px;line-height:1.65;color:#e2e8f0;margin:0 0 12px 0;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">{p_str}</p>')

        body_html = "".join(body_elements)

        # Full Apex Luxury Card Layout
        return f"""<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px;margin:0 auto;background-color:#202225;border:1px solid #36393f;border-radius:14px;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,0.45);">
  <tr>
    <td style="padding:22px 26px;">

      <!-- Top Header Card -->
      <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#273549;border:1px solid #3b82f640;border-radius:10px;margin-bottom:20px;">
        <tr>
          <td style="padding:14px 18px;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="vertical-align:middle;">
                  <div style="font-size:19px;font-weight:700;color:#ffffff;line-height:1.2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">{cand_name}</div>
                  <div style="font-size:12.5px;color:#94a3b8;margin-top:4px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">{cand_title} &bull; {exp_years}+ Years Experience</div>
                </td>
                <td style="text-align:right;vertical-align:middle;">
                  <span style="display:inline-block;border:1px solid #3b82f6;color:#60a5fa;font-size:9.5px;font-weight:700;padding:4px 11px;border-radius:20px;letter-spacing:0.5px;text-transform:uppercase;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">EXECUTIVE CANDIDATE</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Body Content -->
      {body_html}

      <!-- Divider -->
      <div style="border-top:1px solid #334155;margin:16px 0;"></div>

      <!-- Key Technical Competencies Badges -->
      <div style="font-size:10.5px;font-weight:700;color:#94a3b8;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:8px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        KEY TECHNICAL COMPETENCIES:
      </div>
      <div style="margin-bottom:16px;">
        {pills_html}
      </div>

      <!-- Bottom Executive Avatar Card -->
      <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#1a2230;border:1px solid #334155;border-radius:10px;margin-bottom:10px;">
        <tr>
          <td style="padding:12px 14px;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td style="width:44px;vertical-align:middle;">
                  <div style="width:38px;height:38px;border-radius:50%;background-color:#2563eb;color:#ffffff;font-weight:700;font-size:14px;text-align:center;line-height:38px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
                    {initials}
                  </div>
                </td>
                <td style="vertical-align:middle;padding-left:8px;">
                  <div style="font-size:14px;font-weight:700;color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">{cand_name}</div>
                  <div style="font-size:12px;color:#94a3b8;margin-top:2px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">{cand_title}</div>
                  <div style="font-size:12px;margin-top:3px;">
                    <a href="mailto:{cand_email}" style="color:#60a5fa;text-decoration:none;font-weight:500;">✉ {cand_email}</a> &nbsp;&bull;&nbsp; 
                    <a href="tel:{clean_phone_link}" style="color:#4ade80;text-decoration:none;font-weight:500;">📞 {cand_phone}</a>
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Attached Document Banner Card -->
      <div style="background-color:#1e293b;border-left:3px solid #3b82f6;border-radius:6px;padding:8px 12px;color:#94a3b8;font-size:12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        <span style="color:#ffffff;font-weight:600;">&#128196; Attached Document:</span> Professional Resume ({clean_cv_doc_name}_CV.pdf)
      </div>

    </td>
  </tr>
</table>"""

    @classmethod
    def _format_paragraph(cls, p: str, accent: str, bg_accent: str) -> str:
        """Format a single paragraph into HTML with clean typography and maximum inbox deliverability."""
        import re

        # Handle inline/block bullet lists (Key qualifications I bring: - 15+ years... - Expert-level...)
        if " - " in p or p.strip().startswith("- "):
            lines = p.split("\n")
            out = []
            for l in lines:
                l_str = l.strip()
                if not l_str:
                    continue
                if " - " in l_str or l_str.startswith("- "):
                    parts = [pt.strip() for pt in re.split(r'(?:^|\s+)-\s+', l_str) if pt.strip()]
                    if parts:
                        if not l_str.startswith("- ") and len(parts) > 1 and ":" in parts[0]:
                            out.append(f'<p style="margin:14px 0 6px;font-size:15px;font-weight:700;color:#0f172a;line-height:1.6;">{parts[0]}</p>')
                            bullet_pts = parts[1:]
                        else:
                            bullet_pts = parts
                        
                        items_html = "".join(f'<li style="margin:6px 0;color:#334155;font-size:14.5px;line-height:1.65;">{b}</li>' for b in bullet_pts)
                        out.append(f'<ul style="margin:8px 0 16px;padding-left:22px;list-style-type:disc;">{items_html}</ul>')
                else:
                    out.append(f'<p style="margin:14px 0;font-size:15px;color:#1e293b;line-height:1.7;">{l_str}</p>')
            if out:
                return "".join(out)

        # Handle lines with arrows (e.g., Reliability → ..., Efficiency → ...)
        if "→" in p:
            lines = [l.strip() for l in p.split("\n") if l.strip()]
            items = []
            for l in lines:
                if "→" in l:
                    parts = l.split("→", 1)
                    items.append(
                        f'<li style="margin:6px 0;color:#334155;font-size:14.5px;line-height:1.65;">'
                        f'<strong style="color:#0f172a;">{parts[0].strip()}:</strong> '
                        f'<span>{parts[1].strip()}</span></li>'
                    )
                else:
                    items.append(f'<p style="margin:12px 0;font-size:15px;color:#1e293b;line-height:1.7;">{l}</p>')
            return f'<ul style="margin:10px 0 16px;padding-left:22px;list-style-type:disc;">' + "".join(items) + '</ul>'

        # Bullet lists (- ...)
        if p.startswith("- "):
            items = "".join(
                f'<li style="margin:6px 0;color:#334155;font-size:14.5px;line-height:1.65;">{l[2:].strip()}</li>'
                for l in p.split("\n")
                if l.strip().startswith("- ")
            )
            return f'<ul style="margin:12px 0 16px;padding-left:22px;list-style-type:disc;">{items}</ul>'

        # Numbered sections (01. 02. 03.)
        if re.match(r"^\d{2}\.", p):
            lines = p.split("\n")
            title_line = lines[0]
            desc_content = []
            for l in lines[1:]:
                l_str = l.strip()
                if not l_str:
                    continue
                if l_str.startswith("- "):
                    desc_content.append(f'<li style="margin:4px 0;color:#334155;font-size:14.5px;line-height:1.65;">{l_str[2:]}</li>')
                else:
                    desc_content.append(f'<p style="margin:4px 0;color:#1e293b;font-size:15px;line-height:1.65;">{l_str}</p>')
            body_inner = "".join(desc_content)
            if "<li>" in body_inner:
                body_inner = f'<ul style="margin:6px 0;padding-left:20px;list-style-type:disc;">{body_inner}</ul>'
            return (
                f'<div style="margin:14px 0;padding:12px 16px;background-color:#f8fafc;border-left:3px solid #2563eb;border-radius:6px;">'
                f'<strong style="color:#0f172a;font-size:14.5px;display:block;margin-bottom:6px;">{title_line}</strong>'
                f'{body_inner}</div>'
            )

        # Key-value pairs (PROVEN EXPERTISE: ...)
        if ": " in p.split("\n")[0] and p.split("\n")[0].split(": ")[0].isupper():
            lines = p.split("\n")
            formatted = []
            for line in lines:
                parts = line.split(": ", 1)
                if len(parts) == 2 and parts[0].strip().isupper():
                    formatted.append(
                        f'<p style="margin:10px 0;font-size:15px;line-height:1.7;">'
                        f'<strong style="color:#0f172a;">{parts[0]}:</strong> '
                        f'<span style="color:#334155;">{parts[1]}</span></p>'
                    )
                else:
                    formatted.append(f'<p style="margin:10px 0;font-size:15px;color:#1e293b;line-height:1.7;">{line}</p>')
            return "".join(formatted)

        # Arrow items (▸ ...)
        if p.startswith("▸"):
            items = "".join(
                f'<div style="margin:6px 0;padding:8px 12px;background-color:{bg_accent};border-left:3px solid {accent};'
                f'color:#334155;font-size:14px;line-height:1.6;border-radius:4px;">{l.strip()}</div>'
                for l in p.split("\n")
                if l.strip().startswith("▸")
            )
            return f'<div style="margin:12px 0;">{items}</div>'

        # Signature block (only matches true contact info line with email or website/phone, avoiding body paragraphs with "15+ years")
        if ("@" in p or "|" in p or "http" in p) and len(p.split("\n")) <= 3 and not re.search(r"\d+\+?\s*years", p, re.IGNORECASE):
            lines = [l.strip() for l in p.split("\n") if l.strip()]
            if not lines:
                return f'<p style="margin:14px 0;font-size:15px;color:#1e293b;line-height:1.7;">{p}</p>'
            
            name_line = lines[0]
            contact_line = " | ".join(lines[1:]) if len(lines) > 1 else ""
            
            if contact_line and contact_line != name_line:
                return (
                    f'<div style="margin-top:24px;padding-top:16px;border-top:2px solid #e2e8f0;">'
                    f'<strong style="color:{accent};font-size:16px;display:block;margin-bottom:4px;">{name_line}</strong>'
                    f'<span style="color:#64748b;font-size:13px;">{contact_line}</span>'
                    f'</div>'
                )
            else:
                return (
                    f'<div style="margin-top:24px;padding-top:16px;border-top:2px solid #e2e8f0;">'
                    f'<strong style="color:{accent};font-size:16px;display:block;">{name_line}</strong>'
                    f'</div>'
                )

        # Regular paragraph — crisp dark slate text (#1e293b), font 15px, line-height 1.7
        return f'<p style="margin:14px 0;font-size:15px;color:#1e293b;line-height:1.7;">{p}</p>'

    # ── Icebreakers ──────────────────────────────────────────────────────────

    @classmethod
    def _get_icebreaker(cls, company: str, title: str, company_info: dict = None) -> str:
        """Generate a natural icebreaker line with dynamic human variation."""
        import random

        c_info = company_info or {}
        if c_info.get("culture"):
            return f"I have followed {company}'s work and appreciate your team's commitment to quality and technical excellence."
        if c_info.get("news"):
            return f"Given {company}'s ongoing growth, I am enthusiastic about the opportunity to contribute directly to your team's upcoming milestones."

        generic_breakers = [
            f"I have been following {company}'s work in the industry and would be excited to bring my experience to your team.",
            f"With {company}'s continued focus on operational excellence, I believe my background can add immediate value to your current initiatives.",
            f"I appreciate {company}'s reputation for innovation and quality, and I look forward to the prospect of contributing to your team's success.",
            f"Given {company}'s trajectory, I am confident that my technical skills and proactive approach align well with your goals for this role.",
            f"I am eager to bring my hands-on experience and problem-solving skills to help support {company}'s expanding operations."
        ]
        return random.choice(generic_breakers)

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

    TEMPLATE_PROFESSIONAL = """Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}.

With over {experience_years} years of progressive experience as a {profession}, I have developed deep expertise in designing, deploying, and managing large-scale enterprise networks across 10+ countries. My technical proficiency spans SD-WAN/SASE architecture, Zero Trust security, multi-cloud networking (AWS/Azure/GCP), and network automation — delivering measurable results in complex environments.

Key qualifications I bring:
- {experience_years}+ years designing and managing enterprise networks across multiple countries (UAE, Saudi Arabia, Qatar, Kuwait, Lebanon, and more)
- Expert-level knowledge of routing/switching (BGP/OSPF/MPLS), SD-WAN (Silver Peak/Viptela), and next-gen security (FortiGate/Palo Alto/Zero Trust)
- Proven track record: Reduced WAN costs by 45% through SD-WAN deployment across 50+ sites, improved application performance by 60%
- Automated network provisioning using Python/Ansible/Terraform, reducing deployment time by 40% and operational overhead by 35%
- Led Zero Trust (ZTNA/SASE) implementation securing 2,000+ remote users across 30+ branch offices
- Core skills: {skills}

{icebreaker}

I would welcome the opportunity to discuss how my background can contribute to {company}'s continued success. I am available for an interview at your earliest convenience.

Best regards,
{name}
{email}
{phone}
{address}"""

    TEMPLATE_RESULTS = """Dear {company} Hiring Team,

I am reaching out to express my high-level interest in the {title} position at {company}.

My approach is built specifically for organizations that demand reliability, efficiency, and scalable operations from their network and infrastructure teams.

01. PROFESSIONAL EXPERIENCE
{experience_years}+ years as a {profession} designing and managing multi-site enterprise networks across 10+ countries. Consistently maintained 99.99% uptime while delivering impactful infrastructure transformations.

02. CORE COMPETENCIES
- SD-WAN/SASE/ZTNA architecture and deployment (50+ sites, 45% cost reduction)
- Multi-cloud networking (AWS Direct Connect, Azure ExpressRoute, GCP Interconnect)
- Network automation (Python/Ansible/Terraform — 40% faster deployments)
- Enterprise security (FortiGate/Palo Alto/Zero Trust — 2,000+ remote users secured)
- Skills include: {skills}

03. INFRASTRUCTURE OPTIMIZATION
Proven track record of standardizing operational procedures, automating repetitive tasks, and reducing annual operational costs by $500K+ through vendor consolidation and intelligent licensing.

{icebreaker}

"I am committed to bringing rigorous accountability, technical excellence, and structured growth to the {company} team."

I have attached my Professional CV for your comprehensive review. I look forward to discussing how my expertise can drive your infrastructure goals.

Best regards,
{name}
{email}
{phone}
{address}"""

    TEMPLATE_MODERN = """Dear Hiring Team,

I am {name}, a {profession} with {experience_years}+ years of hands-on experience delivering high-quality results across enterprise networking, security, and cloud infrastructure.

Why me for {title} at {company}?

PROVEN EXPERTISE: With over {experience_years} years spanning 10+ countries, I have successfully architected SD-WAN solutions (50+ sites, 45% cost reduction), implemented Zero Trust security for 2,000+ users, and led cloud migrations with 99.99% uptime.

CORE SKILLS: My primary areas of expertise include: {skills}.

AUTOMATION & EFFICIENCY: I focus on structured, results-oriented approaches — automating network provisioning with Python/Ansible/Terraform, reducing deployment time by 40% and operational overhead by 35%.

{icebreaker}

I am immediately available and ready to contribute from day one. Let's discuss how my skills align with your needs.

{name}
{email} | {phone}
LinkedIn: {linkedin}"""

    TEMPLATE_EXECUTIVE = """Dear {company} Leadership,

{title} — {name}

As an experienced {profession} with {experience_years}+ years of cross-functional expertise spanning enterprise networking, security, cloud, and automation across 10+ countries, I am compelled by the opportunity at {company}.

TRACK RECORD OF IMPACT:
▸ Designed and deployed SD-WAN solution across 50+ sites — reduced WAN costs by 45%, improved application performance by 60%
▸ Implemented Zero Trust Network Access (ZTNA/SASE) architecture securing 2,000+ remote users across 30+ branch offices
▸ Led cloud migration of 100+ servers to AWS/Azure with 99.99% uptime and zero security incidents
▸ Automated network provisioning using Python/Ansible/Terraform — reduced deployment time by 40%, operational overhead by 35%
▸ Managed $5M+ network infrastructure budget including vendor negotiations and lifecycle management
▸ Led SOC/NOC team of 12 engineers, establishing 24/7 monitoring with Splunk/ELK SIEM — reduced MTTR by 55%

PROFESSIONAL DEPTH:
▸ Core competencies: {skills}
▸ Focus on strategic planning, operational excellence, and digital transformation

{icebreaker}

I bring the operational discipline, technical depth, and strategic vision that {company} needs at this stage of growth. I look forward to a conversation.

{name}
{email} | {phone} | {linkedin}"""

    TEMPLATE_CONCISE = """Dear Hiring Manager,

Re: {title} at {company}

In {experience_years} years as a {profession} across 10+ countries, I've learned that network excellence comes down to three things. Here's how I deliver each:

Reliability → Designed multi-site MPLS/VPN backbone connecting 200+ locations with 99.99% uptime and BGP/OSPF route optimization
Efficiency → Automated network provisioning with Python/Ansible/Terraform, cutting deployment time by 40% and annual costs by $500K+
Adaptability → Core skills include: {skills}

{icebreaker}

My CV is attached. I'd welcome 15 minutes to discuss how this experience maps to your needs.

{name}
{email} | {phone}"""

    ALL_TEMPLATES = [
        TEMPLATE_PROFESSIONAL,
        TEMPLATE_RESULTS,
        TEMPLATE_MODERN,
        TEMPLATE_EXECUTIVE,
        TEMPLATE_CONCISE,
    ]

    # ── Arabic Cover Letter Template ─────────────────────────────────────────

    TEMPLATE_ARABIC = """السيد/ة مدير التوظيف المحترم،

أكتب إليكم للتعبير عن اهتمامي الكبير بمنصب {title} في {company}.

أملك أكثر من {experience_years} عاماً من الخبرة المتقدمة في مجال الشبكات والأمن السيبراني والحوسبة السحابية عبر 10 دول منها الإمارات والسعودية وقطر والكويت ولبنان. قمت بتصميم وتنفيذ حلول SD-WAN عبر 50 موقعاً مما خفض التكاليف بنسبة 45%، وتطبيق بنية Zero Trust لتأمين أكثر من 2000 مستخدم عن بعد.

المؤهلات الرئيسية:
- أكثر من {experience_years} عاماً من الخبرة في تصميم وإدارة الشبكات المؤسسية
- خبير في SD-WAN، SASE، ZTNA، الحوسبة السحابية (AWS/Azure/GCP)، وأتمتة الشبكات
- سجل حافل: تخفيض تكاليف WAN بنسبة 45%، أتمتة البنية التحتية بنسبة 40% أسرع
- إدارة ميزانية شبكات تتجاوز $5M مع تحقيق توفير سنوي $500K+
- قيادة فريق من 12 مهندس شبكات وأمن معلومات
- مهارات أساسية تشمل: {skills}

{icebreaker}

أرحب بفرصة مناقشة كيف يمكن لخبرتي أن تساهم في نجاح {company} المستمر.

مع خالص التحيات،
{name}
{email}
{phone}
{address}"""

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
        """Generate an AI-personalized cover letter. Falls back to templates if AI fails.

        Args:
            company: Company name
            title: Job title
            description: Job description text
            company_info: Optional company research dict
            language: "en", "ar", "bilingual", or None (auto-detect for ME companies)
        """
        # Auto-detect language for Middle East companies
        if language is None:
            language = cls._detect_language(company, description)

        try:
            # [SILICON VALLEY TRICK] Fetch global winning keywords
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

            # Try AI-generated cover letter
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

        # Fallback to template
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
        """Synchronous cover letter generation (template-based, for backward compatibility)."""
        import config

        ud = user_details or {}
        c_info = company_info
        if isinstance(company_info, dict) and any(k in company_info for k in ("name", "email", "skills", "profession", "phone", "cv_text")):
            ud = {**company_info, **ud}
            c_info = None

        if language is None:
            language = cls._detect_language(company, description)

        if language in ("ar", "bilingual"):
            # Use Arabic template for ME companies
            return cls._write_template_fallback(
                company, title, description, c_info, language, user_details=ud
            )

        template = cls.TEMPLATE_CONCISE
        icebreaker = cls._get_icebreaker(company, title, c_info)

        raw_s = ud.get("skills") or getattr(config, "CANDIDATE_SKILLS", None) or getattr(config, "SKILLS", [])[:10]
        if isinstance(raw_s, list):
            skills_val = ", ".join([str(x) for x in raw_s])
        else:
            skills_val = str(raw_s or "Networking, Cloud, Security, Automation")
        name_val = ud.get("name") or getattr(config, "CANDIDATE_NAME", "Job Applicant")
        email_val = ud.get("email") or getattr(config, "CANDIDATE_EMAIL", "")
        from core.validators import clean_phone_number
        phone_val = clean_phone_number(ud.get("phone") or getattr(config, "CANDIDATE_PHONE", ""))
        address_val = ud.get("address") or getattr(config, "CANDIDATE_ADDRESS", "")
        linkedin_val = ud.get("linkedin") or getattr(config, "CANDIDATE_LINKEDIN", "")
        profession_val = ud.get("profession") or getattr(config, "PROFESSION", "Software Engineer")
        exp_val = str(ud.get("experience_years") or getattr(config, "EXPERIENCE_YEARS", "3"))

        return template.format(
            title=title,
            company=company,
            name=name_val,
            icebreaker=icebreaker,
            email=email_val,
            phone=phone_val,
            address=address_val,
            linkedin=linkedin_val,
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
        """Convert a cover letter to professional HTML. If ai_letter is provided, use it directly."""
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
    # PA template: max 200 words, no AI, no icebreaker — instant generation

    PA_TEMPLATE = """Dear Hiring Manager,

I am writing to apply for the {title} position at {company}.

With {experience_years}+ years of experience as a {profession}, I bring deep expertise to my role and a track record of delivering high-quality results. My core skills include: {skills}.

My CV is available upon request. I would welcome the opportunity to discuss how my experience can contribute to {company}'s success.

Best regards,
{name}
{email} | {phone}"""

    @classmethod
    def write_html_pa(cls, company: str, title: str, user_details: dict = None) -> str:
        """
        ⚡ PA-optimized cover letter: max 200 words, instant template, no AI.
        Returns HTML string directly.
        """
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

    @classmethod
    def _detect_language(cls, company: str, description: str = "") -> str:
        """Auto-detect if bilingual/Arabic cover letter is needed for Middle East companies."""
        text = (company + " " + description).lower()
        for indicator in MIDDLE_EAST_INDICATORS:
            if indicator in text:
                return "bilingual"
        return "en"

    # ── Template Fallback ────────────────────────────────────────────────────

    @classmethod
    def _write_template_fallback(
        cls,
        company: str,
        title: str,
        description: str,
        company_info: dict,
        language: str,
        user_details: dict = None,
    ) -> str:
        """Generate a cover letter using templates when AI is unavailable."""
        import config
        from core.validators import clean_phone_number

        ud = user_details or {}
        c_info = company_info
        if isinstance(company_info, dict) and any(k in company_info for k in ("name", "email", "skills", "profession", "phone", "cv_text")):
            ud = {**company_info, **ud}
            c_info = None

        icebreaker = cls._get_icebreaker(company, title, c_info)

        name = ud.get("name") or config.CANDIDATE_NAME
        email = ud.get("email") or config.CANDIDATE_EMAIL
        phone = clean_phone_number(ud.get("phone") or config.CANDIDATE_PHONE)
        address = config.CANDIDATE_ADDRESS
        linkedin = ud.get("linkedin") or config.CANDIDATE_LINKEDIN
        profession = ud.get("profession") or "Professional"
        skills = ud.get("skills") or "Strong analytical and technical skills"
        experience_years = ud.get("experience_years") or 5

        import random

        if language == "ar":
            return cls.TEMPLATE_ARABIC.format(
                title=title,
                company=company,
                icebreaker=icebreaker,
                name=name,
                email=email,
                phone=phone,
                address=address,
                profession=profession,
                skills=skills,
                experience_years=experience_years,
            )
        elif language == "bilingual":
            ar_letter = cls.TEMPLATE_ARABIC.format(
                title=title,
                company=company,
                icebreaker=icebreaker,
                name=name,
                email=email,
                phone=phone,
                address=address,
                profession=profession,
                skills=skills,
                experience_years=experience_years,
            )
            en_template = cls.TEMPLATE_CONCISE
            en_letter = en_template.format(
                title=title,
                company=company,
                name=name,
                icebreaker=icebreaker,
                email=email,
                phone=phone,
                address=address,
                linkedin=linkedin,
                profession=profession,
                skills=skills,
                experience_years=experience_years,
            )
            return f"{ar_letter}\n\n{'─' * 50}\n\n{en_letter}"
        else:
            template = cls.TEMPLATE_CONCISE
            return template.format(
                title=title,
                company=company,
                name=name,
                icebreaker=icebreaker,
                email=email,
                phone=phone,
                address=address,
                linkedin=linkedin,
                profession=profession,
                skills=skills,
                experience_years=experience_years,
            )

    # ── HTML Conversion ──────────────────────────────────────────────────────

    @classmethod
    def _text_to_html(cls, text: str, company: str, language: str = "en", user_details: dict = None) -> str:
        """Convert plain text cover letter to premium Executive Application HTML email."""
        import config

        import re
        ud = user_details or {}
        cand_name = ud.get("name") or getattr(config, "CANDIDATE_NAME", "Sam Salameh") or "Sam Salameh"
        if cand_name.lower() in ("sam", "candidate", "executive", ""):
            cand_name = "Sam Salameh"
        
        cand_email = ud.get("email") or getattr(config, "CANDIDATE_EMAIL", "sam.dev1@hotmail.com") or "sam.dev1@hotmail.com"
        if not cand_email or "samatou" in cand_email.lower() or "samsalameh.cv" in cand_email.lower():
            cand_email = "sam.dev1@hotmail.com"
        from core.validators import clean_phone_number
        cand_phone = clean_phone_number(ud.get("phone") or getattr(config, "CANDIDATE_PHONE", "+961 70 841 009"))
        
        cand_title = ud.get("profession") or "Senior Software Engineer"
        if not cand_title or "network" in cand_title.lower() or cand_title.lower() in ("professional", ""):
            cand_title = "Senior Software Engineer"
        elif not cand_title.lower().startswith("senior"):
            cand_title = f"Senior {cand_title}"
        exp_years = str(ud.get("experience_years") or "15")

        # Strip any trailing plain-text signatures (e.g. Best regards, Sam Salameh...) to prevent double signature
        pattern_sig = r'\n+(?:Best regards|Sincerely|Kind regards|Regards|Best)?[\s,]*\n?(?:' + re.escape(cand_name) + r'|Sam Salameh|sam\.dev1).*$'
        text = re.sub(pattern_sig, '', text, flags=re.DOTALL | re.IGNORECASE).strip()

        is_bilingual = language in ("bilingual", "ar")
        accent = "#2563eb" if not is_bilingual else "#d97706"
        bg_accent = "#f8fafc" if not is_bilingual else "#fffbeb"

        sections = text.split("─" * 30) if "─" * 30 in text else [text]

        html_parts = []
        for idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            if len(sections) > 1:
                lang_label = "العربية" if idx == 0 else "English"
                html_parts.append(
                    f'<div style="text-align:center;margin:20px 0 10px;">'
                    f'<span style="background:{accent};color:#ffffff;padding:4px 16px;border-radius:12px;'
                    f'font-size:12px;font-weight:700;">{lang_label}</span></div>'
                )

            paragraphs = section.split("\n\n")
            cleaned_paragraphs = []
            for p in paragraphs:
                p_str = p.strip()
                if not p_str:
                    continue
                # Skip raw redundant signature lines (e.g. "Best regards, Sam Salameh sam.dev1@hotmail.com...")
                if re.match(r'^(?:Best regards|Sincerely|Kind regards|Regards|Best)[,\s]*\n?.*(?:Sam Salameh|sam\.dev1)', p_str, re.IGNORECASE):
                    continue
                cleaned_paragraphs.append(p_str)

            for p in cleaned_paragraphs:
                html_parts.append(cls._format_paragraph(p, accent, bg_accent))

        body_content = "".join(html_parts)
        
        # Build Skill Pills if skills exist
        raw_skills = ud.get("skills") or "Python, Software Engineering, Cloud Systems"
        if "cisco" in str(raw_skills).lower() or "mikrotik" in str(raw_skills).lower() or "network engineering" in str(raw_skills).lower():
            raw_skills = "Python, Software Engineering, Cloud Systems"
        if isinstance(raw_skills, list):
            skills_list = [str(s).strip() for s in raw_skills if str(s).strip()][:8]
        else:
            skills_list = [s.strip() for s in str(raw_skills).split(",") if s.strip()][:8]
        skill_pills = "".join(
            f'<span style="display:inline-block;background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe;'
            f'padding:4px 10px;border-radius:14px;font-size:12px;font-weight:600;margin:3px 3px 3px 0;">{s}</span>'
            for s in skills_list
        )

        # Executive Header Banner
        header_banner = (
            f'<div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px 28px; '
            f'border-radius: 12px 12px 0 0; border-bottom: 4px solid #2563eb;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>'
            f'<td style="vertical-align: middle;">'
            f'<h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff; font-family: Arial, sans-serif;">{cand_name}</h1>'
            f'<p style="margin: 4px 0 0; font-size: 13px; color: #94a3b8; font-weight: 500;">{cand_title} &bull; {exp_years}+ Years Experience</p>'
            f'</td>'
            f'<td style="text-align: right; vertical-align: middle;">'
            f'<span style="background: rgba(37, 99, 235, 0.25); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.4); '
            f'padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Executive Candidate</span>'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'</div>'
        )

        # Executive Footer Signature Card
        footer_card = (
            f'<div style="margin-top: 28px; padding: 20px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>'
            f'<td width="48" style="vertical-align: middle;">'
            f'<div style="width: 44px; height: 44px; background: #2563eb; color: #ffffff; border-radius: 50%; '
            f'font-size: 16px; font-weight: 700; text-align: center; line-height: 44px; font-family: Arial, sans-serif;">SS</div>'
            f'</td>'
            f'<td style="padding-left: 14px; vertical-align: middle;">'
            f'<strong style="font-size: 15px; color: #0f172a; display: block; font-family: Arial, sans-serif;">{cand_name}</strong>'
            f'<span style="font-size: 13px; color: #64748b; display: block;">{cand_title}</span>'
            f'<span style="font-size: 12px; color: #2563eb; font-weight: 600; display: block; margin-top: 2px;">{cand_email} &bull; {cand_phone}</span>'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'</div>'
            f'<div style="margin-top: 12px; padding: 12px 16px; background: #eff6ff; border-left: 4px solid #2563eb; border-radius: 6px; font-size: 12px; color: #1e40af; font-family: Arial, sans-serif;">'
            f'📄 <strong>Attached Document:</strong> Complete Professional Resume ({cand_name.replace(" ", "_")}_CV.pdf)'
            f'</div>'
        )

        # Full Executive Email Wrapper
        return (
            f'<div style="font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; '
            f'max-width: 660px; margin: 0 auto; background-color: #ffffff; color: #1e293b; border-radius: 12px; '
            f'border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08); overflow: hidden;">'
            f'{header_banner}'
            f'<div style="padding: 28px;">'
            f'{body_content}'
            f'<div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #f1f5f9;">'
            f'<strong style="font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 8px;">Key Technical Competencies:</strong>'
            f'{skill_pills}'
            f'</div>'
            f'{footer_card}'
            f'</div>'
            f'</div>'
        )

    @classmethod
    def _format_paragraph(cls, p: str, accent: str, bg_accent: str) -> str:
        """Format a single paragraph into HTML with smart styling and crisp readability."""
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
                        
                        items_html = "".join(f'<li style="margin:6px 0;color:#334155;font-size:14px;line-height:1.7;">{b}</li>' for b in bullet_pts)
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
                        f'<div style="margin:8px 0;padding:10px 14px;background:{bg_accent};border-left:3px solid {accent};border-radius:6px;">'
                        f'<strong style="color:{accent};font-size:14px;">{parts[0].strip()} →</strong> '
                        f'<span style="color:#334155;font-size:14px;line-height:1.6;">{parts[1].strip()}</span></div>'
                    )
                else:
                    items.append(f'<p style="margin:12px 0;font-size:15px;color:#1e293b;line-height:1.7;">{l}</p>')
            return "".join(items)

        # Bullet lists (- ...)
        if p.startswith("- "):
            items = "".join(
                f'<li style="margin:6px 0;color:#334155;font-size:14px;line-height:1.7;">{l[2:].strip()}</li>'
                for l in p.split("\n")
                if l.strip().startswith("- ")
            )
            return f'<ul style="margin:16px 0;padding-left:20px;list-style-type:disc;">{items}</ul>'

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
                    desc_content.append(f'<li style="margin:4px 0;color:#1e293b;font-size:14px;line-height:1.6;">{l_str[2:]}</li>')
                else:
                    desc_content.append(f'<div style="margin:4px 0;color:#1e293b;font-size:14px;line-height:1.6;">{l_str}</div>')
            body_inner = "".join(desc_content)
            if "<li>" in body_inner:
                body_inner = f'<ul style="margin:6px 0;padding-left:18px;list-style-type:disc;">{body_inner}</ul>'
            return (
                f'<div style="margin:14px 0;padding:16px 18px;background:{bg_accent};'
                f'border-left:4px solid {accent};border-radius:8px;">'
                f'<strong style="color:{accent};font-size:15px;display:block;margin-bottom:8px;">{title_line}</strong>'
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
                        f'<div style="margin:10px 0;">'
                        f'<strong style="color:{accent};font-size:14px;">{parts[0]}:</strong> '
                        f'<span style="color:#334155;font-size:14px;line-height:1.6;">{parts[1]}</span></div>'
                    )
                else:
                    formatted.append(
                        f'<p style="margin:14px 0;font-size:15px;color:#1e293b;line-height:1.7;">{line}</p>'
                    )
            return "".join(formatted)

        # Arrow items (▸ ...)
        if p.startswith("▸"):
            items = "".join(
                f'<div style="margin:6px 0;padding:8px 12px;background:{bg_accent};border-left:3px solid {accent};'
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
    def _get_icebreaker(cls, company: str, title: str, company_info: dict) -> str:
        """Generate an icebreaker line. Uses company info if available."""
        breakers = []
        if company_info:
            if company_info.get("info"):
                breakers.append(
                    f"I have been following {company}'s recent developments and impressive growth in the industry, particularly in the networking and infrastructure space."
                )
            if company_info.get("culture"):
                breakers.append(
                    f"{company}'s commitment to innovation and technical excellence resonates deeply with my professional values and engineering philosophy."
                )
            if company_info.get("news"):
                breakers.append(
                    "Your latest infrastructure and technology projects demonstrate exactly the kind of technical challenges I have thrived on throughout my 15-year career."
                )
            if company_info.get("values"):
                breakers.append(
                    f"{company}'s values of {company_info['values'][:50]} align closely with how I approach network engineering challenges — with precision, reliability, and continuous improvement."
                )
        if not breakers:
            return f"With {company}'s continued growth and focus on digital transformation, I believe my expertise in network automation, cloud networking, and security architecture would be immediately valuable."
        return breakers[0]

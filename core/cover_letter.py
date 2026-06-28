"""
CoverLetterWriter v2 - AI-Powered with Template Fallback
Integrates with AITailor for personalized cover letters.
Falls back to enhanced HTML templates when AI is unavailable.
Supports Arabic/English bilingual cover letters for Middle East companies.
"""
import random
import logging
import asyncio
import re
import config
from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)

# ── Middle East country indicators for bilingual support ─────────────────────
MIDDLE_EAST_INDICATORS = [
    "uae", "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "al ain",
    "qatar", "doha", "lusail", "al wakrah",
    "saudi", "riyadh", "jeddah", "mecca", "medina", "dammam", "khobar", "dhahran",
    "kuwait", "kuwait city", "hawalli", "salmiya",
    "oman", "muscat", "salalah", "sohar", "nizwa",
    "bahrain", "manama", "muharraq",
    "iraq", "baghdad", "basra", "erbil",
    "gcc", "gulf", "middle east", "mena",
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

A senior {profession} with {experience_years}+ years of cross-functional expertise spanning enterprise networking, security, cloud, and automation across 10+ countries, I am compelled by the opportunity at {company}.

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

    ALL_TEMPLATES = [TEMPLATE_PROFESSIONAL, TEMPLATE_RESULTS, TEMPLATE_MODERN, TEMPLATE_EXECUTIVE, TEMPLATE_CONCISE]

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
    async def write_ai(cls, company: str, title: str, description: str = "",
                       company_info: dict = None, language: str = None) -> str:
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
                hive_mind_keywords = await predictive_engine.get_hive_mind_keywords(company)
                if hive_mind_keywords:
                    if company_info is None:
                        company_info = {}
                    company_info["values"] = company_info.get("values", "") + f" [HIVE MIND SUCCESS KEYWORDS TO INCLUDE: {hive_mind_keywords}]"
            except Exception as e:
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
            logger.warning(f"AI cover letter failed for {company}: {e}, falling back to template")

        # Fallback to template
        return cls._write_template_fallback(company, title, description, company_info, language)

    @classmethod
    def write(cls, company: str, title: str, company_info=None, description: str = "",
              language: str = None) -> str:
        """Synchronous cover letter generation (template-based, for backward compatibility)."""
        if language is None:
            language = cls._detect_language(company, description)

        if language in ("ar", "bilingual"):
            # Use Arabic template for ME companies
            return cls._write_template_fallback(company, title, description, company_info, language)

        template = random.choice(cls.ALL_TEMPLATES)
        icebreaker = cls._get_icebreaker(company, title, company_info)
        return template.format(
            title=title, company=company, name=config.CANDIDATE_NAME,
            icebreaker=icebreaker, email=config.CANDIDATE_EMAIL,
            phone=config.CANDIDATE_PHONE, address=config.CANDIDATE_ADDRESS,
            linkedin=config.CANDIDATE_LINKEDIN,
            profession=getattr(config, 'PROFESSION', 'Software Engineer'),
            experience_years=getattr(config, 'EXPERIENCE_YEARS', '3')
        )

    @classmethod
    def write_html(cls, company: str, title: str, company_info=None,
                   description: str = "", language: str = None,
                   ai_letter: str = None) -> str:
        """Convert a cover letter to professional HTML. If ai_letter is provided, use it directly."""
        if language is None:
            language = cls._detect_language(company, description)

        if ai_letter:
            text = ai_letter
        else:
            text = cls.write(company, title, company_info, description, language)

        return cls._text_to_html(text, company, language)

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
        ud = user_details or {}
        name = ud.get("name") or config.CANDIDATE_NAME
        email = ud.get("email") or config.CANDIDATE_EMAIL
        phone = ud.get("phone") or config.CANDIDATE_PHONE
        profession = ud.get("profession") or "Professional"
        skills = ud.get("skills") or "Strong analytical and technical skills"
        experience_years = ud.get("experience_years") or 5

        text = cls.PA_TEMPLATE.format(
            title=title, company=company,
            name=name, email=email, phone=phone,
            profession=profession, skills=skills, experience_years=experience_years
        )
        return cls._text_to_html(text, company, "en")

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
    def _write_template_fallback(cls, company: str, title: str, description: str,
                                  company_info: dict, language: str, user_details: dict = None) -> str:
        """Generate a cover letter using templates when AI is unavailable."""
        import config
        icebreaker = cls._get_icebreaker(company, title, company_info)
        ud = user_details or {}
        
        name = ud.get("name") or config.CANDIDATE_NAME
        email = ud.get("email") or config.CANDIDATE_EMAIL
        phone = ud.get("phone") or config.CANDIDATE_PHONE
        address = config.CANDIDATE_ADDRESS
        linkedin = ud.get("linkedin") or config.CANDIDATE_LINKEDIN
        profession = ud.get("profession") or "Professional"
        skills = ud.get("skills") or "Strong analytical and technical skills"
        experience_years = ud.get("experience_years") or 5

        import random

        if language == "ar":
            return cls.TEMPLATE_ARABIC.format(
                title=title, company=company, icebreaker=icebreaker,
                name=name, email=email, phone=phone, address=address,
                profession=profession, skills=skills, experience_years=experience_years
            )
        elif language == "bilingual":
            ar_letter = cls.TEMPLATE_ARABIC.format(
                title=title, company=company, icebreaker=icebreaker,
                name=name, email=email, phone=phone, address=address,
                profession=profession, skills=skills, experience_years=experience_years
            )
            en_template = random.choice(cls.ALL_TEMPLATES)
            en_letter = en_template.format(
                title=title, company=company, name=name,
                icebreaker=icebreaker, email=email,
                phone=phone, address=address,
                linkedin=linkedin, profession=profession, 
                skills=skills, experience_years=experience_years
            )
            return f"{ar_letter}\n\n{'─' * 50}\n\n{en_letter}"
        else:
            template = random.choice(cls.ALL_TEMPLATES)
            return template.format(
                title=title, company=company, name=name,
                icebreaker=icebreaker, email=email,
                phone=phone, address=address,
                linkedin=linkedin, profession=profession, 
                skills=skills, experience_years=experience_years
            )

    # ── HTML Conversion ──────────────────────────────────────────────────────

    @classmethod
    def _text_to_html(cls, text: str, company: str, language: str = "en") -> str:
        """Convert plain text cover letter to styled HTML matching the reference email template.
        No wrapper div — content renders directly inside the EmailBuilder <td>."""
        is_bilingual = language in ("bilingual", "ar")

        # Color scheme — reference accent
        accent = "#00b4d8" if not is_bilingual else "#d4a853"
        bg_accent = f"rgba(0, 180, 216, 0.05)" if not is_bilingual else f"rgba(212, 168, 83, 0.05)"

        # Split into sections (by horizontal rule for bilingual)
        if "─" * 30 in text:
            sections = text.split("─" * 30)
        else:
            sections = [text]

        html_parts = []
        for idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            # Add language label for bilingual
            if len(sections) > 1:
                lang_label = "العربية" if idx == 0 else "English"
                html_parts.append(
                    f'<div style="text-align:center;margin:20px 0 10px;">'
                    f'<span style="background:{accent};color:white;padding:4px 16px;border-radius:12px;'
                    f'font-size:12px;font-weight:600;">{lang_label}</span></div>'
                )

            paragraphs = section.split("\n\n")
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                html_parts.append(cls._format_paragraph(p, accent, bg_accent))

        # No wrapper div — just the content parts directly
        return "".join(html_parts)

    @classmethod
    def _format_paragraph(cls, p: str, accent: str, bg_accent: str) -> str:
        """Format a single paragraph into HTML with smart styling."""
        # Bullet lists
        if p.startswith("- "):
            items = "".join(
                f'<li style="margin:6px 0;color:#e2e8f0;font-size:15px;line-height:1.8;">{l[2:]}</li>'
                for l in p.split("\n") if l.startswith("- ")
            )
            return f'<ul style="margin:20px 0;padding-left:20px;list-style:none;">{items}</ul>'

        # Numbered sections (01. 02. 03.)
        if re.match(r'^\d{2}\.', p):
            lines = p.split("\n")
            title_line = lines[0]
            desc_lines = " ".join(lines[1:]) if len(lines) > 1 else ""
            return (
                f'<div style="margin:10px 0;padding:15px;background:{bg_accent};'
                f'border-left:4px solid {accent};">'
                f'<strong style="color:{accent};">{title_line}</strong><br>'
                f'<span style="color:#b8c5d0;font-size:13px;line-height:1.6;">{desc_lines}</span></div>'
            )

        # Key-value pairs (PROVEN EXPERTISE: ...)
        if ": " in p.split("\n")[0] and p.split("\n")[0].split(": ")[0].isupper():
            lines = p.split("\n")
            formatted = []
            for line in lines:
                parts = line.split(": ", 1)
                if len(parts) == 2 and parts[0].strip().isupper():
                    formatted.append(
                        f'<div style="margin:8px 0;">'
                        f'<strong style="color:{accent};">{parts[0]}:</strong> '
                        f'<span style="color:#e2e8f0;">{parts[1]}</span></div>'
                    )
                else:
                    formatted.append(
                        f'<p style="margin:20px 0;font-size:15px;color:#e2e8f0;'
                        f'line-height:1.8;">{line}</p>'
                    )
            return "".join(formatted)

        # Arrow items (▸ ...)
        if p.startswith("▸"):
            items = "".join(
                f'<div style="margin:6px 0;padding-left:8px;border-left:3px solid {accent};'
                f'color:#e2e8f0;font-size:15px;line-height:1.8;">{l.strip()}</div>'
                for l in p.split("\n") if l.strip().startswith("▸")
            )
            return f'<div style="margin:10px 0;">{items}</div>'

        # Signature block
        if "Sam Salameh" in p and ("|" in p or "@" in p):
            lines = p.split("\n")
            name_line = lines[0] if lines else p
            contact_lines = lines[1:] if len(lines) > 1 else []
            contact_html = "<br>".join(
                f'<span style="color:#94a3b8;font-size:13px;">{l.strip()}</span>'
                for l in contact_lines
            )
            return (
                f'<div style="margin-top:20px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.1);">'
                f'<strong style="color:{accent};font-size:16px;">{name_line}</strong><br>'
                f'{contact_html}</div>'
            )

        # Regular paragraph — reference font 15px, line-height 1.8
        return f'<p style="margin:20px 0;font-size:15px;color:#e2e8f0;line-height:1.8;">{p}</p>'

    # ── Icebreakers ──────────────────────────────────────────────────────────

    @classmethod
    def _get_icebreaker(cls, company: str, title: str, company_info: dict) -> str:
        """Generate an icebreaker line. Uses company info if available."""
        breakers = []
        if company_info:
            if company_info.get('info'):
                breakers.append(
                    f"I have been following {company}'s recent developments and impressive growth in the industry, particularly in the networking and infrastructure space."
                )
            if company_info.get('culture'):
                breakers.append(
                    f"{company}'s commitment to innovation and technical excellence resonates deeply with my professional values and engineering philosophy."
                )
            if company_info.get('news'):
                breakers.append(
                    f"Your latest infrastructure and technology projects demonstrate exactly the kind of technical challenges I have thrived on throughout my 15-year career."
                )
            if company_info.get('values'):
                breakers.append(
                    f"{company}'s values of {company_info['values'][:50]} align closely with how I approach network engineering challenges — with precision, reliability, and continuous improvement."
                )
        if not breakers:
            breakers = [
                f"I am particularly drawn to this opportunity at {company} because it aligns perfectly with my 15+ years of expertise in SD-WAN, enterprise networking, and security architecture.",
                f"The {title} role at {company} represents an ideal match for my extensive experience designing and managing multi-site networks across 10+ countries.",
                f"{company}'s reputation for technical excellence in the networking space makes this an exciting opportunity for my next career step.",
                f"The technical challenges at {company} are exactly the kind that have defined my career — from SD-WAN deployments across 50+ sites to Zero Trust security implementations for thousands of users.",
                f"Having designed and managed enterprise networks across the Middle East and beyond for 15+ years, I am excited about the opportunity to bring this experience to {company}.",
                f"With {company}'s continued growth and focus on digital transformation, I believe my expertise in network automation, cloud networking, and security architecture would be immediately valuable.",
            ]
        return random.choice(breakers)

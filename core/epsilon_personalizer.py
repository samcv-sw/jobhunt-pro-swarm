"""
Publicis Epsilon & Dentsu Merkle Inspired Hyper-Personalization Engine — DCO Module
Performs deep lead enrichment, persona targeting, industry contextualization,
and dynamic creative optimization (DCO) for 10x campaign outreach conversion.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class EpsilonHyperPersonalizer:
    """
    Hyper-Personalization & Dynamic Creative Optimization Engine.
    Employs multi-tier persona mapping, industry intelligence hooks,
    and Gulf/Global cultural ergonomics.
    """

    INDUSTRY_HOOKS: Dict[str, Dict[str, str]] = {
        "finance": {
            "pain_point": "optimizing yield, risk-weighted asset allocation, and regulatory compliance",
            "value_prop": "delivering sub-millisecond execution clarity, institutional risk telemetry, and measurable bottom-line growth",
            "tone": "executive, analytical, numbers-driven"
        },
        "tech": {
            "pain_point": "scaling distributed architecture, reducing technical debt, and accelerating deployment velocity",
            "value_prop": "engineering zero-downtime microservices, AI swarm integration, and 10x developer productivity",
            "tone": "innovative, direct, metrics-focused"
        },
        "healthcare": {
            "pain_point": "HIPAA compliance, operational workflow optimization, and clinical efficiency",
            "value_prop": "streamlining patient-centric data pipelines and compliant administrative AI swarms",
            "tone": "empathic, rigorous, compliant"
        },
        "energy": {
            "pain_point": "operational resilience, ESG target tracking, and supply chain continuity",
            "value_prop": "driving capital efficiency, asset optimization, and zero-defect operational execution",
            "tone": "strategic, robust, long-term"
        },
        "default": {
            "pain_point": "scaling revenue pipelines, securing top-tier leadership, and streamlining operations",
            "value_prop": "delivering end-to-end autonomous efficiency, strategic execution, and measurable ROI",
            "tone": "professional, persuasive, results-oriented"
        }
    }

    PERSONA_HOOKS: Dict[str, Dict[str, str]] = {
        "c_suite": {
            "salutation": "Dear",
            "hook_prefix": "Looking at your strategic leadership at {company},",
            "cta": "Would you be open to a brief 10-minute executive briefing this week?",
            "focus": "High-level ROI, capital allocation, market dominance"
        },
        "hr_leader": {
            "salutation": "Hello",
            "hook_prefix": "Given your focus on talent acquisition and organizational excellence at {company},",
            "cta": "Let's schedule a 5-minute call to show you how we eliminate 90% of manual recruiter workload.",
            "focus": "Retention, candidate quality, time-to-hire reduction"
        },
        "tech_lead": {
            "salutation": "Hi",
            "hook_prefix": "Impressed by {company}'s tech stack and engineering velocity,",
            "cta": "Care to inspect our architectural benchmark performance dashboard?",
            "focus": "Performance benchmarks, clean architecture, zero technical debt"
        },
        "default": {
            "salutation": "Dear",
            "hook_prefix": "I was following {company}'s recent growth in the market,",
            "cta": "Would you be open to exploring synergies this week?",
            "focus": "Efficiency, growth, value creation"
        }
    }

    def detect_industry(self, text: str) -> str:
        """Detect industry from target company description or domain."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["bank", "fintech", "asset", "trading", "capital", "investment", "finance"]):
            return "finance"
        if any(w in text_lower for w in ["software", "ai", "cloud", "saas", "tech", "data", "cyber"]):
            return "tech"
        if any(w in text_lower for w in ["health", "pharma", "medical", "clinic", "biotech"]):
            return "healthcare"
        if any(w in text_lower for w in ["oil", "gas", "energy", "solar", "renewable", "grid"]):
            return "energy"
        return "default"

    def detect_persona(self, title: str) -> str:
        """Detect target persona level from job title."""
        t_lower = title.lower()
        if any(w in t_lower for w in ["ceo", "cto", "cfo", "chief", "founder", "president", "managing director", "vp", "vice president"]):
            return "c_suite"
        if any(w in t_lower for w in ["hr", "talent", "recruiter", "people", "chro", "staffing"]):
            return "hr_leader"
        if any(w in t_lower for w in ["lead", "head of engineering", "architect", "principal", "engineering manager"]):
            return "tech_lead"
        return "default"

    def generate_dco_copy(
        self,
        lead_name: str,
        company_name: str,
        job_title: str,
        company_summary: str = "",
        custom_notes: str = ""
    ) -> Dict[str, str]:
        """
        Generates dynamic creative optimization (DCO) email copy customized to recipient persona and industry.
        """
        industry = self.detect_industry(company_summary or company_name)
        persona = self.detect_persona(job_title)

        ind_info = self.INDUSTRY_HOOKS.get(industry, self.INDUSTRY_HOOKS["default"])
        per_info = self.PERSONA_HOOKS.get(persona, self.PERSONA_HOOKS["default"])

        salutation = f"{per_info['salutation']} {lead_name.split()[0] if lead_name else 'Colleague'}"
        hook = per_info["hook_prefix"].format(company=company_name or "your organization")

        subject_options = [
            f"Strategic Talent & ROI Optimization for {company_name}",
            f"{company_name} x Executive Talent Intelligence",
            f"Accelerating {company_name}'s Q3 Hiring Velocity"
        ]

        body = (
            f"{salutation},\n\n"
            f"{hook} I wanted to reach out directly regarding {ind_info['pain_point']}.\n\n"
            f"Our platform is purpose-built for {per_info['focus'].lower()}, "
            f"enabling organizations to achieve {ind_info['value_prop']}.\n\n"
            f"{custom_notes + ' ' if custom_notes else ''}"
            f"{per_info['cta']}\n\n"
            f"Best regards,\n"
            f"Executive Relations Team\n"
            f"JobHunt Pro SaaS"
        )

        return {
            "subject": subject_options[0],
            "body": body,
            "detected_industry": industry,
            "detected_persona": persona,
            "tone": ind_info["tone"]
        }

    REGIONAL_PSYCHOMETRICS: Dict[str, Dict[str, str]] = {
        "gulf": {
            "tone_description": "High executive respect, formal Arabic/English greetings, corporate authority",
            "salutation_ar": "سعادة الأستاذ / الأستاذة المحترمين",
            "closing_ar": "مع خالص التقدير والاحترام لجهودكم المتميزة،",
            "value_emphasis": "strategic alignment with Vision 2030 / UAE digital economy, enterprise stability, and regional market leadership",
        },
        "us": {
            "tone_description": "Direct, fast-paced, high ROI, measurable metric orientation",
            "salutation_ar": "تحياتي،",
            "closing_ar": "تحياتي الحارة،",
            "value_emphasis": "3x engineering velocity, immediate bottom-line revenue impact, and scalable infrastructure",
        },
        "europe": {
            "tone_description": "Methodical, structured, process-oriented, compliance & quality driven",
            "salutation_ar": "حضرة الزملاء الأعزاء،",
            "closing_ar": "وتفضلوا بقبول فائق الاحترام،",
            "value_emphasis": "robust architecture, zero technical debt, ISO/GDPR compliant standards, and long-term sustainability",
        },
    }

    def inject_portfolio_evidence(
        self,
        key_skills: List[str],
        github_url: str = "https://github.com/samde",
        portfolio_url: str = "https://jobhuntpro.io/portfolio/sam",
    ) -> str:
        """
        Dynamically constructs verified code/project snippets tailored to target tech requirements.
        """
        if not key_skills:
            return f"Explore verified production repositories & live architecture benchmarks at {github_url}."

        top_skill = key_skills[0]
        return (
            f"Here is a direct demonstration of production-grade {top_skill} systems: {github_url} "
            f"and interactive benchmark case studies: {portfolio_url}."
        )

    def generate_multilingual_pitch(
        self,
        candidate_name: str,
        target_role: str,
        company_name: str,
        language: str = "ar",
        region: str = "gulf",
        key_skills: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generates flawless Arabic, English, or French executive SDR pitches aligned with regional psychometrics.
        """
        skills = key_skills or ["FastAPI", "Python", "Cloud Architecture"]
        skills_str = "، ".join(skills[:3]) if language == "ar" else ", ".join(skills[:3])
        portfolio_text = self.inject_portfolio_evidence(skills)

        if language == "ar":
            subject = f"طلب انضمام مهني متميز • {target_role} — {candidate_name}"
            body = (
                f"{self.REGIONAL_PSYCHOMETRICS.get(region, self.REGIONAL_PSYCHOMETRICS['gulf'])['salutation_ar']} لدى {company_name}،\n\n"
                f"يطيب لي التواصل معكم انطلاقاً من متابعتي لنجاحاتكم ومشاريعكم الرائدة. "
                f"أتقدم إليكم كـ {target_role} متخصص في بناء وتطوير الأنظمة عالية الكفاءة ({skills_str}).\n\n"
                f"أمتلك سجلاً حافلاً في قيادة المشاريع التقنية والارتقاء بالأداء ومواءمة الأهداف الإستراتيجية. "
                f"يسعدني مشاركتكم نماذج حية من الأعمال والمشاريع البرمجية عبر الرابط: {portfolio_text}\n\n"
                f"أتطلع بكل سرور لفرصة حوار موجز لبحث آفاق التعاون وتقديم قيمة مضافة فورية لفريقكم الموقر.\n\n"
                f"{self.REGIONAL_PSYCHOMETRICS.get(region, self.REGIONAL_PSYCHOMETRICS['gulf'])['closing_ar']}\n"
                f"{candidate_name}"
            )
        elif language == "fr":
            subject = f"Candidature spontanée : {target_role} — {candidate_name}"
            body = (
                f"Madame, Monsieur,\n\n"
                f"Fort d'une solide expertise en ingénierie logicielle et architecture système ({skills_str}), "
                f"je me permets de vous soumettre ma candidature pour le poste de {target_role} au sein de {company_name}.\n\n"
                f"Démonstrations techniques et projets : {portfolio_text}\n\n"
                f"Je reste à votre entière disposition pour convenir d'un échange.\n\n"
                f"Cordialement,\n{candidate_name}"
            )
        else:
            subject = f"Introduction: {target_role} Application — {candidate_name}"
            body = (
                f"Hello {company_name} Talent Team,\n\n"
                f"I am reaching out regarding technical opportunities for {target_role}. "
                f"With deep expertise in {skills_str}, I specialize in building resilient, high-throughput architectures.\n\n"
                f"Code demonstrations & benchmarks: {portfolio_text}\n\n"
                f"Looking forward to connecting briefly.\n\n"
                f"Best regards,\n{candidate_name}"
            )

        return {
            "subject": subject,
            "body": body,
            "language": language,
            "region": region,
        }

# Global Instance
epsilon_personalizer = EpsilonHyperPersonalizer()

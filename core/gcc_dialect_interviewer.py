"""
GCC Dialect & Corporate Persona AI Interviewer Engine
JobHunt Pro SaaS - Simulates realistic hiring committee personas across Saudi, UAE & Qatar.
"""
from typing import Dict, List, Any, Optional


class GccDialectInterviewer:
    """
    Simulates authentic GCC executive interviewers with regional corporate terminology,
    cultural greetings, and tough technical/behavioral probe questions.
    """

    PERSONAS = {
        "saudi_executive": {
            "name": "المهندس فهد العتيبي (مدير تنفيذي - الرياض)",
            "organization_type": "Mega Projects & Sovereign Funds (NEOM / PIF / Aramco)",
            "dialect": "Saudi Najdi / Formal Business Arabic",
            "greeting_ar": "حياك الله أستاذي الكريم، سعيدين بوجودك معنا اليوم ضمن مقابلات المشاريع الوطنية الكبرى.",
            "greeting_en": "Welcome. We are glad to have you with us for this strategic role aligned with Vision 2030 initiatives.",
            "core_focus": "Local Content (محتوى محلي), Strategic Leadership, Vision 2030 Alignment, Scale",
            "sample_questions_ar": [
                "حدثنا عن مشروع معقد قمت بقيادته، وكيف وازنت بين الجودة وسرعة التسليم في بيئة عمل سريعة التغير؟",
                "كيف تتعامل مع توطين المعرفة وبناء وتدريب الكفاءات الشابة ضمن فريقك التقني؟",
                "ما هي خطتك الاستراتيجية خلال أول 90 يوماً في حال انضمامك لقيادة هذا القطاع؟"
            ]
        },
        "emirati_tech_lead": {
            "name": "م. راشد النعيمي (Head of Engineering - Dubai)",
            "organization_type": "Gulf Tech Scale-ups & Digital Unicorns (Dubai AI Hub)",
            "dialect": "Emirati Bilingual (Gulf Arabic + Tech English)",
            "greeting_ar": "مرحبا الساع، منور معنا اليوم! نبغي نعرف أكثر عن خبرتك في الـ High-Scale Architecture وكيف تطور الأنظمة.",
            "greeting_en": "Welcome! We are looking forward to diving deep into your distributed systems experience and execution velocity.",
            "core_focus": "Scalability, Latency, CI/CD, ROI, Cloud Infrastructure",
            "sample_questions_ar": [
                "كلمنا عن أكبر Incident صار عندك في الـ Production وكيف حليت الـ Root Cause بدون Downtime؟",
                "كيف تقيس الـ KPIs للـ Engineering Team وتضمن إن الـ Delivery ماشي على الـ Roadmap؟",
                "شو هي التحديات التقنية اللي تتوقع تواجهها في بيئة سريعة النمو مثل دبي؟"
            ]
        },
        "qatari_fintech_director": {
            "name": "د. حمد الكواري (مدير الابتكار المالي - الدوحة)",
            "organization_type": "Banking, Energy & Sovereign Enterprise",
            "dialect": "Qatari Formal Business Arabic",
            "greeting_ar": "أهلاً ومرحباً بك، نتشرف بحضورك لمناقشة هذا الدور القيادي في قطاعنا المالي.",
            "greeting_en": "Welcome. We are pleased to discuss this mission-critical leadership role with you.",
            "core_focus": "Cybersecurity Compliance, Risk Mitigation, Enterprise Governance",
            "sample_questions_ar": [
                "كيف تضمن الامتثال الصارم لمعايير الأمن السيبراني وحماية بيانات العملاء عند تصميم الحلول السحابية؟",
                "حدثنا عن تجربة سابقة في إدارة المخاطر التقنية أثناء التحول الرقمي لأنظمة بنكية أو حكومية حساسة؟"
            ]
        }
    }

    @classmethod
    def get_available_personas(cls) -> Dict[str, Any]:
        """Returns all configured regional interviewer personas."""
        return {
            key: {
                "name": val["name"],
                "organization_type": val["organization_type"],
                "dialect": val["dialect"],
                "core_focus": val["core_focus"]
            }
            for key, val in cls.PERSONAS.items()
        }

    @classmethod
    def generate_interview_round(
        cls,
        persona_key: str = "saudi_executive",
        candidate_role: str = "Enterprise Cloud Architect",
        round_number: int = 1
    ) -> Dict[str, Any]:
        """Generates persona-specific greeting, probing questions, and evaluation criteria."""
        persona = cls.PERSONAS.get(persona_key, cls.PERSONAS["saudi_executive"])
        q_list = persona["sample_questions_ar"]
        selected_q = q_list[(round_number - 1) % len(q_list)]

        return {
            "persona_key": persona_key,
            "interviewer_name": persona["name"],
            "organization_tier": persona["organization_type"],
            "dialect_style": persona["dialect"],
            "greeting_text": persona["greeting_ar"],
            "greeting_text_en": persona["greeting_en"],
            "current_question": selected_q,
            "evaluation_focus": persona["core_focus"],
            "recommended_response_framework": "STAR Framework (Situation, Task, Action, Result) with quantified GCC impact."
        }


# Global singleton instance
gcc_dialect_interviewer = GccDialectInterviewer()

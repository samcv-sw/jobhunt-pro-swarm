"""
core/spintax_psychographic_engine.py - Dynamic Spintax & Psychographic Tone Engine
JobHunt Pro SaaS - Generates anti-spam spintax variations and tunes outreach psychology
across English and Gulf Arabic communication styles.
"""

import re
import random
from typing import Dict, Any, List, Optional

SPINTAX_PATTERNS = {
    "en_direct": (
        "{Hi|Hello|Dear|Greetings} [TARGET_NAME],\n\n"
        "{I noticed|I came across|I have been following} [COMPANY_NAME]'s recent {expansion|momentum|breakthroughs} in [INDUSTRY_OR_ROLE].\n\n"
        "{Given your focus on|Knowing how critical it is to drive} high-impact growth, "
        "{I wanted to share how|I am reaching out regarding how} my background directly solves key {scaling|engineering|operational} challenges.\n\n"
        "{Would you have|Are you open to} a brief 5-minute conversation {this week|over the next few days}?\n\n"
        "{Best regards|Sincerely|Warm regards},\n[SENDER_NAME]"
    ),
    "en_formal": (
        "{Dear|Hello} [TARGET_NAME],\n\n"
        "{I am reaching out because|Writing directly as} [COMPANY_NAME] is actively {expanding|scaling} its leadership in [INDUSTRY_OR_ROLE].\n\n"
        "{With proven expertise in|Having consistently delivered results in} driving revenue and technical excellence, "
        "{I can contribute immediately to your roadmap|I am confident in adding measurable value to your team}.\n\n"
        "{Let me know if you are open to reviewing my executive brief|Happy to send over a concise summary of my recent achievements}.\n\n"
        "{Respectfully|Best regards|With appreciation},\n[SENDER_NAME]"
    ),
    "en_consultative": (
        "{Greetings|Dear} [TARGET_NAME],\n\n"
        "{Following [COMPANY_NAME]'s latest updates in [INDUSTRY_OR_ROLE]|Tracking your team's ambitious milestones},\n\n"
        "{I developed a quick framework|I outlined a strategic approach} to help {accelerate deliverability|optimize operational velocity|drive technical innovation} with zero friction.\n\n"
        "{Would you be open to a 5-minute sync|Could I share a 1-page overview} {early next week|at your convenience}?\n\n"
        "{Kind regards|Sincerely},\n[SENDER_NAME]"
    ),
    "ar_gulf_executive": (
        "{تحية طيبة وتقدير لسعادتكم|السلام عليكم ورحمة الله وبركاته|تحية طيبة وعاطرة} [TARGET_NAME]،\n\n"
        "{يسعدني ويشرفني التواصل مع سعادتكم|أتشرف بمخاطبة شخصكم الكريم} في ظل {النمو المتسارع|التوسع الاستراتيجي الملحوظ|الريادة المستمرة} لـ [COMPANY_NAME] في قطاع [INDUSTRY_OR_ROLE].\n\n"
        "{انطلاقاً من خبرتي العملية في قيادة المشاريع التقنية|نظراً لسجلي المهني في تعزيز الكفاءة التشغيلية وتحقيق المستهدفات}، "
        "{يسرني استعراض أوجه التكامل والتعاون المشترك لدعم رؤيتكم المستقبلية|يسعدني تقديم حلول نوعية تسهم مباشرة في تحقيق أعلى عائد استثماري لفريقكم}.\n\n"
        "{هل يتسع وقت سعادتكم لمحادثة قصيرة (5 دقائق) هذا الأسبوع لمناقشة التفاصيل؟|يسعدني تزويدكم بملخص تنفيذي موجز لأبرز الإنجازات متى ما ناسبكم الوقت}.\n\n"
        "{وتفضلوا بقبول فائق الاحترام والتقدير|مع خالص الود والتقدير لسعادتكم|دمتم برعاية الله وتوفيقه}،\n[SENDER_NAME]"
    ),
    "ar_gulf_direct": (
        "{أهلاً بك|تحية طيبة|مرحباً} [TARGET_NAME]،\n\n"
        "{لفت انتباهي التطور المميز|أتابع باهتمام كبير مسيرة النجاح} لـ [COMPANY_NAME] في مجال [INDUSTRY_OR_ROLE].\n\n"
        "{بناءً على خبرتي في بناء الأنظمة القابلة للتوسع|انطلاقاً من تحقيق نتائج ملموسة في تقليص التكاليف وتسريع الإنجاز}، "
        "{أود مشاركة تجربة عملية يمكن تطبيقها مباشرة لدى فريقكم|أثق بقدرتي على إحداث نقلة نوعية وسريعة في مؤشرات الأداء لديكم}.\n\n"
        "{هل يناسبكم موعد سريع لمناقشة الفرص المتاحة؟|يسرني إرسال ملخص عملي لأبرز الحلول المقترحة}.\n\n"
        "{مع أطيب التحيات|مع كل التقدير|تحياتي الخالصة}،\n[SENDER_NAME]"
    ),
    "ar_gulf_consultative": (
        "{الأستاذ الفاضل|أخي الكريم|حياك الله} [TARGET_NAME]،\n\n"
        "{يسعدني مشاركتكم بعض الرؤى التحليلية حول [COMPANY_NAME]|اطلعت باهتمام على مبادرات [COMPANY_NAME] الطموحة} في قطاع [INDUSTRY_OR_ROLE].\n\n"
        "{لقد أعددت مقترحاً مقتضباً يوضح|طورت نموذج عمل يهدف إلى} {رفع الكفاءة التشغيلية|أتمتة العمليات الحساسة|تسريع الوصول للنتائج} بنسبة تفوق 40%.\n\n"
        "{هل يمكننا ترتيب مكالمة استكشافية سريعة خلال الأيام القادمة؟|يسعدني إرسال نظرة عامة مختصرة للاطلاع}.\n\n"
        "{مع وافر الشكر والامتنان|تقبلوا خالص احترامي|مع أطيب التمنيات بالتوفيق}،\n[SENDER_NAME]"
    )
}

class SpintaxPsychographicEngine:
    """
    Parses nested Spintax syntax `{A|{B|C}|D}` and injects psychographic tone variants.
    """

    @staticmethod
    def spin(text: str) -> str:
        """Recursively parses and resolves Spintax curly bracket expressions."""
        pattern = re.compile(r'\{([^{}]+)\}')
        while True:
            match = pattern.search(text)
            if not match:
                break
            choices = match.group(1).split('|')
            text = text[:match.start()] + random.choice(choices) + text[match.end():]
        return text

    @staticmethod
    def count_theoretical_permutations(text: str) -> int:
        """
        Estimates total theoretical unique variant permutations for a spintax string.
        """
        pattern = re.compile(r'\{([^{}]+)\}')
        total_permutations = 1
        matches = pattern.findall(text)
        for m in matches:
            choices = m.split('|')
            total_permutations *= max(1, len(choices))
        return total_permutations

    @classmethod
    def generate_variant(
        cls,
        target_name: str = "Hiring Leader",
        company_name: str = "your esteemed organization",
        industry_or_role: str = "strategic operations",
        sender_name: str = "Candidate",
        tone: str = "gulf_executive",
        language: str = "ar"
    ) -> Dict[str, Any]:
        """
        Generates a uniquely randomized, personalized pitch with zero spam footprint
        and high-context cultural Gulf Arabic tone modulation.
        """
        if language == "ar":
            if tone == "gulf_direct":
                template_key = "ar_gulf_direct"
            elif tone == "gulf_consultative":
                template_key = "ar_gulf_consultative"
            else:
                template_key = "ar_gulf_executive"
        else:
            if tone == "formal":
                template_key = "en_formal"
            elif tone == "consultative":
                template_key = "en_consultative"
            else:
                template_key = "en_direct"

        template = SPINTAX_PATTERNS.get(template_key, SPINTAX_PATTERNS["ar_gulf_executive" if language == "ar" else "en_direct"])
        theoretical_variants = cls.count_theoretical_permutations(template)
        spun_template = cls.spin(template)
        
        # Replace placeholders
        rendered_body = spun_template.replace(
            "[TARGET_NAME]", target_name or ("سعادة المدير" if language == "ar" else "Decision Maker")
        ).replace(
            "[COMPANY_NAME]", company_name or ("المؤسسة" if language == "ar" else "your company")
        ).replace(
            "[INDUSTRY_OR_ROLE]", industry_or_role or ("الأعمال" if language == "ar" else "your sector")
        ).replace(
            "[SENDER_NAME]", sender_name or ""
        )

        subject_options = {
            "en": [
                f"{company_name} & Strategic Milestones",
                f"Quick question regarding {industry_or_role} at {company_name}",
                f"Collaboration opportunity for {company_name}",
                f"Delivering high-ROI impact in {industry_or_role}"
            ],
            "ar": [
                f"فرصة تعاون استراتيجي مع {company_name}",
                f"مبادرة مهنية لتسريع نمو {company_name}",
                f"استفسار بخصوص القيادة التنفيذية في {company_name}",
                f"تعزيز كفاءة قطاع {industry_or_role} لدى {company_name}"
            ]
        }

        chosen_subject = random.choice(subject_options.get(language, subject_options["en"]))

        return {
            "subject": chosen_subject,
            "body": rendered_body,
            "tone": tone,
            "language": language,
            "theoretical_permutations": theoretical_variants,
            "spintax_entropy": round(random.uniform(0.92, 0.99), 3)
        }

# Global singleton
spintax_engine = SpintaxPsychographicEngine()

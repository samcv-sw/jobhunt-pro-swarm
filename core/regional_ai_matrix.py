"""
core/regional_ai_matrix.py
Sovereign Regional AI Matrix & Cultural Prompt Adaptation Engine
JobHunt Pro SaaS — Multi-Region Sovereign LLM Routing (China, USA, Russia/CIS, GCC/MENA, Global)

Features:
1. Intelligent Locale & Geo Detection (Language, TLD, Location name, Company Domain).
2. Dynamic Region-Specific Model Topology:
   - China / APAC: Qwen 2.5 / DeepSeek-V3 / ERNIE / Moonshot
   - CIS / Russia: YandexGPT / GigaChat / Llama 3.3 CIS
   - US / EU: Groq Llama 3.3 70B / Claude 3.5 / Gemini 2.0 Flash
   - GCC / MENA: Arabic Dialect & Cultural Ergonomics (Saudi, Emirati, Egyptian, Levantine)
3. Specialized Regional System Prompts & Pitch Structuring.
4. Fail-safe fallback to global free-tier pool.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger("RegionalAIMatrix")


class MarketRegion(str, Enum):
    CHINA_APAC = "china_apac"
    CIS_RUSSIA = "cis_russia"
    US_EU_AMERICAS = "us_eu_americas"
    GCC_MENA = "gcc_mena"
    GLOBAL = "global"


# Regional Model Configuration
REGIONAL_MODELS: Dict[MarketRegion, List[Dict[str, Any]]] = {
    MarketRegion.CHINA_APAC: [
        {"model": "qwen-2.5-72b", "provider": "dashscope/groq", "context_window": 32768, "primary": True},
        {"model": "deepseek-chat", "provider": "deepseek", "context_window": 64000, "primary": False},
        {"model": "moonshot-v1-32k", "provider": "moonshot", "context_window": 32768, "primary": False},
        {"model": "ernie-4.0", "provider": "baidu", "context_window": 8192, "primary": False},
    ],
    MarketRegion.CIS_RUSSIA: [
        {"model": "yandexgpt-pro", "provider": "yandex", "context_window": 8192, "primary": True},
        {"model": "gigachat-latest", "provider": "sber", "context_window": 8192, "primary": False},
        {"model": "llama-3.3-70b-versatile", "provider": "groq", "context_window": 8192, "primary": False},
    ],
    MarketRegion.US_EU_AMERICAS: [
        {"model": "llama-3.3-70b-versatile", "provider": "groq", "context_window": 8192, "primary": True},
        {"model": "gemini-2.0-flash", "provider": "google", "context_window": 1048576, "primary": False},
        {"model": "claude-3-5-sonnet-latest", "provider": "anthropic", "context_window": 200000, "primary": False},
        {"model": "mistral-large-latest", "provider": "mistral", "context_window": 32768, "primary": False},
    ],
    MarketRegion.GCC_MENA: [
        {"model": "gemini-2.0-flash", "provider": "google", "context_window": 1048576, "primary": True},
        {"model": "llama-3.3-70b-versatile", "provider": "groq", "context_window": 8192, "primary": False},
        {"model": "deepseek-chat", "provider": "deepseek", "context_window": 64000, "primary": False},
    ],
    MarketRegion.GLOBAL: [
        {"model": "llama-3.3-70b-versatile", "provider": "groq", "context_window": 8192, "primary": True},
        {"model": "gemini-1.5-flash", "provider": "google", "context_window": 1048576, "primary": False},
        {"model": "deepseek-chat", "provider": "deepseek", "context_window": 64000, "primary": False},
    ],
}


class RegionalAIMatrix:
    """
    Sovereign AI Routing Matrix.
    Detects market territory and crafts culturally optimized outreach pitches.
    """

    @staticmethod
    def detect_market_region(
        location: Optional[str] = None,
        company_domain: Optional[str] = None,
        job_text: Optional[str] = None,
        language: Optional[str] = None,
    ) -> MarketRegion:
        """
        Determines the target market region based on multi-signal heuristic analysis.
        """
        combined = f"{location or ''} {company_domain or ''} {job_text or ''} {language or ''}".lower()

        # 1. China / APAC Signals
        if any(w in combined for w in [".cn", ".hk", ".tw", "china", "beijing", "shanghai", "shenzhen", "guangzhou", "hangzhou", "zh-cn", "zh-tw", "chinese", "wechat", "zhipin"]):
            return MarketRegion.CHINA_APAC

        # 2. CIS / Russia Signals
        if any(w in combined for w in [".ru", ".by", ".kz", "russia", "moscow", "saint petersburg", "novosibirsk", "minsk", "almaty", "hh.ru", "superjob", "yandex", "russian"]):
            return MarketRegion.CIS_RUSSIA

        # 3. GCC / MENA Signals
        if any(w in combined for w in [".sa", ".ae", ".qa", ".kw", ".bh", ".om", ".eg", ".lb", "saudi", "riyadh", "dubai", "abu dhabi", "doha", "kuwait", "cairo", "beirut", "arabic", "gcc", "mena"]):
            return MarketRegion.GCC_MENA

        # 4. US / EU / Americas Signals
        if any(w in combined for w in [".com", ".us", ".uk", ".de", ".fr", ".ca", ".io", "united states", "usa", "san francisco", "new york", "london", "berlin", "paris", "toronto"]):
            return MarketRegion.US_EU_AMERICAS

        return MarketRegion.GLOBAL

    @classmethod
    def get_regional_model_tier(cls, region: MarketRegion) -> List[Dict[str, Any]]:
        """Returns the prioritised model hierarchy for the given market region."""
        return REGIONAL_MODELS.get(region, REGIONAL_MODELS[MarketRegion.GLOBAL])

    @classmethod
    def build_culturally_adapted_prompt(
        cls,
        region: MarketRegion,
        candidate_name: str,
        target_role: str,
        recruiter_name: str,
        company_name: str,
        key_skills: List[str],
        pain_point: str = "scaling engineering operations",
        dialect: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Constructs localized, culturally resonant system prompts and user payloads
        tailored specifically for the target business etiquette.
        """
        skills_str = ", ".join(key_skills[:4])

        if region == MarketRegion.CHINA_APAC:
            system_prompt = (
                "You are an elite bilingual executive career agent specializing in Chinese business communication (企业招聘/猎头标准). "
                "Craft a direct, highly respectful, and outcome-oriented pitch suitable for WeChat Work, Maimai, or corporate email. "
                "Emphasize technical mastery, speed of execution, team alignment, and ROI."
            )
            user_prompt = (
                f"Candidate: {candidate_name}\n"
                f"Target Role: {target_role}\n"
                f"Recruiter: {recruiter_name}\n"
                f"Company: {company_name}\n"
                f"Core Competencies: {skills_str}\n"
                f"Company Focus/Challenge: {pain_point}\n"
                "Format: 3 short, punchy paragraphs with clear value proposition and invitation to connect."
            )

        elif region == MarketRegion.CIS_RUSSIA:
            system_prompt = (
                "You are a top-tier tech recruiter and career strategist operating in the CIS/Eastern European market. "
                "Write in clear, structured, and pragmatic tone (деловой стиль, без лишней воды). "
                "Highlight architecture skills, concrete metrics, and proven delivery track record."
            )
            user_prompt = (
                f"Кандидат: {candidate_name}\n"
                f"Позиция: {target_role}\n"
                f"Рекрутер/HR: {recruiter_name}\n"
                f"Компания: {company_name}\n"
                f"Стек/Навыки: {skills_str}\n"
                f"Ключевая задача: {pain_point}\n"
                "Требование: 3 лаконичных абзаца с акцентом на результат и техническую надежность."
            )

        elif region == MarketRegion.GCC_MENA:
            dialect_style = dialect or "Gulf Professional"
            system_prompt = (
                f"You are a senior executive headhunter specializing in the GCC & MENA corporate ecosystem ({dialect_style}). "
                "Ensure maximum cultural elegance, professional esteem, and alignment with regional vision initiatives (Saudi Vision 2030, UAE Digital Economy). "
                "Tone: Respectful, visionary, metric-backed, and confident."
            )
            user_prompt = (
                f"المرشح: {candidate_name}\n"
                f"المسمى المستهدف: {target_role}\n"
                f"المسؤول/الشركة: {recruiter_name} في {company_name}\n"
                f"المهارات والخبرات: {skills_str}\n"
                f"المحور المستهدف: {pain_point}\n"
                "المطلوب: رسالة تقديم احترافية رفيعة المستوى من 3 فقرات مركزة تُبرز القيمة المضافة فوراً."
            )

        elif region == MarketRegion.US_EU_AMERICAS:
            system_prompt = (
                "You are an expert Silicon Valley / European Tech SDR copywriter. "
                "Write in a modern, ultra-concise, frictionless style that respects recruiter time. "
                "Hook them in sentence one with a specific value prop, back it up with metrics, and close with a low-friction CTA."
            )
            user_prompt = (
                f"Candidate: {candidate_name}\n"
                f"Target Role: {target_role}\n"
                f"Recruiter: {recruiter_name}\n"
                f"Company: {company_name}\n"
                f"Skills: {skills_str}\n"
                f"Pain Point: {pain_point}\n"
                "Output: Maximum 100 words, razor-sharp, zero corporate fluff."
            )

        else:
            system_prompt = (
                "You are a global executive career advisor. Craft a universally compelling, polished, and metric-driven outreach message."
            )
            user_prompt = (
                f"Candidate: {candidate_name}\n"
                f"Target Role: {target_role}\n"
                f"Recruiter: {recruiter_name}\n"
                f"Company: {company_name}\n"
                f"Key Skills: {skills_str}\n"
                f"Context: {pain_point}\n"
                "Generate a crisp 3-paragraph executive introduction."
            )

        return {
            "region": region.value,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }


# Global singleton instance
global_regional_ai_matrix = RegionalAIMatrix()

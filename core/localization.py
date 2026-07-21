"""
Global Multi-Language Localization Engine for JobHunt Pro SaaS.
Provides translation dictionary, automatic RTL/LTR detection, and cultural formatting.
"""

import asyncio
from functools import lru_cache
from typing import Dict, Any, Optional

from sqlalchemy import text

from backend.database import async_session
from backend.models import UITextTranslation

SUPPORTED_LANGUAGES = {
    "ar": {"name": "العربية", "dir": "rtl"},
    "en": {"name": "English", "dir": "ltr"},
    "fr": {"name": "Français", "dir": "ltr"},
    "de": {"name": "Deutsch", "dir": "ltr"},
    "es": {"name": "Español", "dir": "ltr"},
    "zh": {"name": "中文", "dir": "ltr"},
    "ja": {"name": "日本語", "dir": "ltr"},
    "ru": {"name": "Русский", "dir": "ltr"},
    "pt": {"name": "Português", "dir": "ltr"},
    "it": {"name": "Italiano", "dir": "ltr"},
    "tr": {"name": "Türkçe", "dir": "ltr"},
    "hi": {"name": "हिन्दी", "dir": "ltr"},
}

# Default fallback translations for critical UI keys
DEFAULT_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "welcome": {
        "ar": "مرحباً بك في المنصة الذكية للتوظيف الجريء",
        "en": "Welcome to JobHunt Pro Sovereign Platform",
        "fr": "Bienvenue sur la plateforme JobHunt Pro",
        "de": "Willkommen bei JobHunt Pro",
        "es": "Bienvenido a JobHunt Pro",
    },
    "welcome_message": {
        "ar": "مرحبا بكم في JobHunt برو",
        "en": "Welcome to JobHunt Pro",
        "fr": "Bienvenue sur JobHunt Pro",
        "es": "Bienvenido a JobHunt Pro",
        "de": "Willkommen bei JobHunt Pro",
        "zh": "欢迎来到JobHunt Pro",
        "ja": "JobHunt Proへようこそ",
        "ru": "Добро пожаловать в JobHunt Pro",
        "pt": "Bem-vindo ao JobHunt Pro",
        "hi": "JobHunt Pro में आपका स्वागत है",
        "it": "Benvenuto su JobHunt Pro",
        "tr": "JobHunt Pro'ya Hoş Geldiniz",
    },
    "dashboard_title": {
        "ar": "لوحة التحكم الرئيسية والتحليلات الحية",
        "en": "Main Dashboard & Real-Time Analytics",
        "fr": "Tableau de bord principal et analyses en temps réel",
        "de": "Haupt-Dashboard & Echtzeit-Analysen",
        "es": "Panel principal y analíticas en tiempo real",
    },
    "start_interview": {
        "ar": "بدء التمرن على المقابلة بالذكاء الاصطناعي",
        "en": "Start AI Mock Interview",
        "fr": "Démarrer l'entretien simulé par IA",
        "de": "AI-Mock-Interview starten",
        "es": "Iniciar entrevista simulada por IA",
    },
    "hidden_jobs": {
        "ar": "الوظائف الحصرية والأنظمة المباشرة",
        "en": "Hidden ATS & Unlisted Jobs Engine",
        "fr": "Moteur d'emplois masqués ATS",
        "de": "Versteckte ATS-Jobs-Engine",
        "es": "Motor de empleos ocultos ATS",
    },
}


class LocalizationEngine:
    """
    Async localization engine with database-backed translations and in-memory caching.
    Provides translation lookup with fallback chain: requested lang -> English -> key.
    """

    def __init__(self, default_lang: str = "ar"):
        self.default_lang = default_lang
        self._cache: Dict[str, Dict[str, str]] = {}
        self._cache_lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Initialize cache with default translations on first use."""
        if not self._initialized:
            async with self._cache_lock:
                if not self._initialized:
                    # Pre-populate cache with default translations
                    for key, translations in DEFAULT_TRANSLATIONS.items():
                        if key not in self._cache:
                            self._cache[key] = translations
                    self._initialized = True

    async def _load_translations_from_db(self) -> Dict[str, Dict[str, str]]:
        """Load all UI text translations from database."""
        translations: Dict[str, Dict[str, str]] = {}
        
        try:
            async with async_session() as session:
                result = await session.execute(
                    text("SELECT key, language_code, value FROM ui_text_translation")
                )
                rows = result.fetchall()
                
                for row in rows:
                    key = row[0]
                    lang = row[1]
                    value = row[2]
                    
                    if key not in translations:
                        translations[key] = {}
                    translations[key][lang] = value
        except Exception as e:
            logger.warning(f"Could not load translations from DB (table may not exist yet): {e}")
        
        return translations

    async def _refresh_cache(self) -> None:
        """Refresh translation cache from database."""
        db_translations = await self._load_translations_from_db()
        
        async with self._cache_lock:
            # Merge with defaults (DB translations take precedence)
            for key, langs in db_translations.items():
                if key not in self._cache:
                    self._cache[key] = {}
                self._cache[key].update(langs)
            
            # Ensure all default keys exist
            for key, langs in DEFAULT_TRANSLATIONS.items():
                if key not in self._cache:
                    self._cache[key] = langs

    def get_text(self, key: str, lang: str = "ar") -> str:
        """
        Get translated text for a key in the specified language.
        
        Args:
            key: The translation key (e.g., 'welcome', 'dashboard_title')
            lang: Target language code (e.g., 'en', 'ar', 'fr')
            
        Returns:
            Translated text, or fallback to English, or the key itself if not found.
        """
        # Validate language
        target_lang = lang if lang in SUPPORTED_LANGUAGES else self.default_lang
        
        # Check cache first
        if key in self._cache:
            if target_lang in self._cache[key]:
                return self._cache[key][target_lang]
            elif "en" in self._cache[key]:
                return self._cache[key]["en"]
        
        # Fallback to default translations
        if key in DEFAULT_TRANSLATIONS:
            if target_lang in DEFAULT_TRANSLATIONS[key]:
                return DEFAULT_TRANSLATIONS[key][target_lang]
            elif "en" in DEFAULT_TRANSLATIONS[key]:
                return DEFAULT_TRANSLATIONS[key]["en"]
        
        return key

    def get_direction(self, lang: str = "ar") -> str:
        """Get text direction (rtl/ltr) for a language."""
        return SUPPORTED_LANGUAGES.get(lang, {}).get("dir", "rtl" if lang == "ar" else "ltr")


    async def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """Get all supported languages with their metadata."""
        return SUPPORTED_LANGUAGES

    async def warm_cache(self) -> None:
        """Warm the translation cache from database (call at startup)."""
        await self._ensure_initialized()
        await self._refresh_cache()

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self._cache.clear()
        self._initialized = False


# Module-level singleton instance
translator = LocalizationEngine()


# Synchronous wrapper for backward compatibility
def get_text_sync(key: str, lang: str = "ar") -> str:
    """
    Synchronous wrapper for get_text.
    Use this for non-async contexts where database access is not available.
    Falls back to default translations only.
    """
    target_lang = lang if lang in SUPPORTED_LANGUAGES else "ar"
    
    if key in DEFAULT_TRANSLATIONS:
        if target_lang in DEFAULT_TRANSLATIONS[key]:
            return DEFAULT_TRANSLATIONS[key][target_lang]
        elif "en" in DEFAULT_TRANSLATIONS[key]:
            return DEFAULT_TRANSLATIONS[key]["en"]
    
    return key


def get_direction_sync(lang: str = "ar") -> str:
    """Synchronous wrapper for get_direction."""
    return SUPPORTED_LANGUAGES.get(lang, {}).get("dir", "rtl" if lang == "ar" else "ltr")


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LanguageMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and set language from request."""

    async def dispatch(self, request: Request, call_next):
        lang = request.query_params.get("lang") or request.cookies.get("lang") or "ar"
        request.state.lang = lang
        request.state.dir = SUPPORTED_LANGUAGES.get(lang, {}).get("dir", "rtl" if lang == "ar" else "ltr")
        response = await call_next(request)
        return response
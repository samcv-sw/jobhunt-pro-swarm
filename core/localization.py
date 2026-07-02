import gettext
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

# Base directory for locales
LOCALES_DIR = Path(__file__).parent.parent / "locales"

# Cache for gettext translation objects to avoid reloading from disk on every request
_translations_cache = {}


def get_translation(lang: str):
    if lang in _translations_cache:
        return _translations_cache[lang]

    try:
        t = gettext.translation(
            "messages", localedir=str(LOCALES_DIR), languages=[lang], fallback=True
        )
    except Exception:
        t = gettext.NullTranslations()

    _translations_cache[lang] = t
    return t


class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Check Query Parameter
        lang = request.query_params.get("lang")

        # 2. Check Cookie
        if not lang:
            lang = request.cookies.get("lang")

        # 3. Check Accept-Language Header (simplified extraction)
        if not lang:
            accept_lang = request.headers.get("accept-language", "")
            if "ar" in accept_lang.lower():
                lang = "ar"
            elif "en" in accept_lang.lower():
                lang = "en"

        # 4. Fallback to default
        if lang not in ["ar", "en"]:
            lang = "ar"  # Default system language

        # Bind to request state
        request.state.locale = lang

        # Get translation object and attach the gettext method
        t = get_translation(lang)
        request.state._ = t.gettext

        response = await call_next(request)
        return response

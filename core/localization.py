import gettext
from pathlib import Path

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

class LanguageMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        request = Request(scope)

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
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["locale"] = lang

        # Get translation object and attach the gettext method
        t = get_translation(lang)
        scope["state"]["_"] = t.gettext

        await self.app(scope, receive, send)

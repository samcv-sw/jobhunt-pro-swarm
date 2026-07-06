from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class I18nMiddleware(BaseHTTPMiddleware):
    """
    Middleware to intercept incoming requests and determine the locale.
    Checks query parameters first (?lang=ar), then cookies, then Accept-Language header.
    Sets request.state.lang and request.state.dir (rtl/ltr) to be used globally.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        lang = "en"  # default
        
        # 1. Check Query Parameter
        if "lang" in request.query_params:
            lang = request.query_params["lang"]
        # 2. Check Cookie
        elif "lang" in request.cookies:
            lang = request.cookies["lang"]
        # 3. Check Accept-Language Header
        else:
            accept_lang = request.headers.get("accept-language", "")
            if accept_lang.startswith("ar"):
                lang = "ar"

        # Sanitize
        if lang not in ["en", "ar"]:
            lang = "en"

        request.state.lang = lang
        request.state.dir = "rtl" if lang == "ar" else "ltr"

        response = await call_next(request)
        
        # If language was changed via query param, set the cookie so it persists
        if "lang" in request.query_params:
            response.set_cookie(key="lang", value=lang, max_age=86400 * 365, httponly=False)
            
        return response

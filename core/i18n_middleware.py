from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send


class I18nMiddleware:
    """
    Pure ASGI middleware to intercept incoming requests and determine the locale.
    Checks query parameters first (?lang=ar), then cookies, then Accept-Language header.
    Sets scope['state']['lang'] and scope['state']['dir'] (rtl/ltr) for use globally.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
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

        # Store in scope state so request.state.lang works normally
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["lang"] = lang
        scope["state"]["dir"] = "rtl" if lang == "ar" else "ltr"

        set_cookie = "lang" in request.query_params

        async def send_with_lang_cookie(message):
            if set_cookie and message["type"] == "http.response.start":
                message = dict(message)
                headers = MutableHeaders(scope=message)
                headers.append(
                    "set-cookie",
                    f"lang={lang}; Max-Age={86400 * 365}; Path=/; SameSite=Lax"
                )
            await send(message)

        await self.app(scope, receive, send_with_lang_cookie)

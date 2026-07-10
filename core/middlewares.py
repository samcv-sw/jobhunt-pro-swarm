import logging

logger = logging.getLogger(__name__)

class PanicModeMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        from starlette.responses import HTMLResponse

        request = Request(scope)
        try:
            from core.pg_sqlite_shim import get_db

            conn = get_db()
            row = conn.execute(
                "SELECT value FROM system_config WHERE key = 'panic_mode'"
            ).fetchone()
            conn.close()

            if row and row["value"].lower() == "true":
                path = request.url.path
                # Allow static assets and admin routes through
                if not (path.startswith("/admin") or path.startswith("/static/")):
                    # Decoy server response
                    decoy_html = """
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Service Maintenance</title>
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f8f9fa; color: #333; }
                            .container { text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; }
                            h1 { color: #2c3e50; font-size: 24px; margin-bottom: 16px; }
                            p { color: #666; line-height: 1.6; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>System Upgrade in Progress</h1>
                            <p>We are currently performing scheduled database maintenance to improve performance and reliability. Service will resume shortly.</p>
                            <p style="font-size: 12px; color: #aaa; margin-top: 24px;">Error Code: 503 Service Unavailable</p>
                        </div>
                    </body>
                    </html>
                    """
                    response = HTMLResponse(content=decoy_html, status_code=503)
                    await response(scope, receive, send)
                    return
        except Exception as e:
            logger.error(f"Panic mode check failed: {e}")

        await self.app(scope, receive, send)

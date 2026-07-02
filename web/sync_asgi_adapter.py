import asyncio
from http import HTTPStatus
import sys
import threading

def build_scope(environ):
    headers = [
        (
            (key[5:] if key.startswith("HTTP_") else key).lower().replace("_", "-").encode("latin-1"),
            value.encode("latin-1"),
        )
        for key, value in environ.items()
        if key.startswith("HTTP_") and key not in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH")
        or key in ("CONTENT_TYPE", "CONTENT_LENGTH")
    ]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.1").split("/")[1],
        "method": environ["REQUEST_METHOD"],
        "scheme": environ.get("wsgi.url_scheme", "http"),
        "path": environ.get("PATH_INFO", "").encode("latin1").decode("utf8") or "/",
        "query_string": environ.get("QUERY_STRING", "").encode("latin-1"),
        "root_path": environ.get("SCRIPT_NAME", "").encode("latin1").decode("utf8"),
        "headers": headers,
        "server": (environ.get("SERVER_NAME", "localhost"), int(environ.get("SERVER_PORT", "80"))),
        "client": (environ.get("REMOTE_ADDR", "127.0.0.1"), 0),
    }
    return scope

_thread_locals = threading.local()

def get_loop():
    if not hasattr(_thread_locals, "loop"):
        _thread_locals.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_thread_locals.loop)
    return _thread_locals.loop

class SyncAsgiToWsgi:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        print(">>> WSGI REQUEST STARTED:", environ.get("PATH_INFO"), file=sys.stderr, flush=True)
        scope = build_scope(environ)
        
        body = b""
        content_length = environ.get("CONTENT_LENGTH", "")
        if content_length:
            try:
                length = int(content_length)
                body = environ["wsgi.input"].read(length)
            except Exception as e:
                print(">>> READ ERROR:", e, file=sys.stderr, flush=True)

        status_code = [200]
        response_headers = []
        response_body = []

        async def run_asgi():
            receive_state = {"sent_request": False}
            response_complete_event = asyncio.Event()

            async def receive():
                if not receive_state["sent_request"]:
                    receive_state["sent_request"] = True
                    return {"type": "http.request", "body": body, "more_body": False}
                await response_complete_event.wait()
                return {"type": "http.disconnect"}

            async def send(message):
                if message["type"] == "http.response.start":
                    status_code[0] = message["status"]
                    for name, value in message.get("headers", []):
                        response_headers.append((name.decode("latin1"), value.decode("latin1")))
                elif message["type"] == "http.response.body":
                    response_body.append(message.get("body", b""))
                    if not message.get("more_body", False):
                        response_complete_event.set()

            try:
                await self.app(scope, receive, send)
            except Exception as e:
                print(">>> ASGI ERROR:", e, file=sys.stderr, flush=True)
                if str(e) != "ClientDisconnect" and "disconnect" not in str(e).lower():
                    status_code[0] = 500
                    response_body.append(str(e).encode("utf8"))

        print(">>> GETTING LOOP", file=sys.stderr, flush=True)
        loop = get_loop()
        print(">>> RUNNING UNTIL COMPLETE", file=sys.stderr, flush=True)
        loop.run_until_complete(run_asgi())
        print(">>> RUN FINISHED", file=sys.stderr, flush=True)

        try:
            status_str = f"{status_code[0]} {HTTPStatus(status_code[0]).phrase}"
        except ValueError:
            status_str = f"{status_code[0]} Unknown"

        print(">>> SENDING START_RESPONSE", file=sys.stderr, flush=True)
        start_response(status_str, response_headers)
        return response_body

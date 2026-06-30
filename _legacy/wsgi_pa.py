"""PythonAnywhere WSGI - JobHunt Pro. ASGI->WSGI bridge for FastAPI."""
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [wsgi_pa] %(message)s"
)
logger = logging.getLogger("wsgi_pa")

PROJECT = '/home/JHFGUF/jobhunt'
if not os.path.exists(PROJECT):
    PROJECT = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Project root: {PROJECT}")

sys.path.insert(0, PROJECT)
os.chdir(PROJECT)
for d in ['data', 'logs', 'sent_mails']:
    os.makedirs(os.path.join(PROJECT, d), exist_ok=True)
import site
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)
    logger.info(f"Added user site-packages: {user_site}")
try:
    import fastapi.dependencies.utils as _fdu
    _fdu.ensure_multipart_is_installed = lambda: None
except Exception:
    pass
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT, '.env'))
logger.info(".env loaded")

# Fix extreme DB latency by forcing local SQLite instead of timing out to Neon PG
os.environ["FORCE_SQLITE"] = "1"
logger.info("FORCE_SQLITE=1 (PA mode: using local SQLite)")

try:
    from web.app_v2 import app as _asgi_app
    logger.info("app_v2 imported successfully")
except Exception as e:
    logger.error(f"Failed to import app_v2: {e}", exc_info=True)
    raise

try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(_asgi_app)
    logger.info("Using a2wsgi ASGIMiddleware bridge")
except ImportError:
    logger.warning("a2wsgi not available — falling back to inline ASGI->WSGI bridge")
    import asyncio
    import io

    class ASGItoWSGI:
        def __init__(self, a): self.asgi_app = a
        def __call__(self, e, s):
            l = asyncio.new_event_loop()
            try: return l.run_until_complete(self._h(e, s))
            finally: l.close()
        async def _h(self, e, s):
            p, q = e.get('PATH_INFO', '/'), e.get('QUERY_STRING', '')
            m = e.get('REQUEST_METHOD', 'GET')
            sv = (e.get('SERVER_NAME', ''), int(e.get('SERVER_PORT', 80)))
            h = []
            for k, v in e.items():
                if k.startswith('HTTP_'): h.append((k[5:].lower().replace('_', '-').encode(), v.encode()))
                elif k == 'CONTENT_TYPE' and v: h.append((b'content-type', v.encode()))
                elif k == 'CONTENT_LENGTH' and v: h.append((b'content-length', v.encode()))
            b = e.get('wsgi.input', io.BytesIO()).read()
            sc = {
                'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                'method': m, 'headers': h, 'path': p, 'query_string': q.encode(),
                'root_path': e.get('SCRIPT_NAME', ''), 'scheme': e.get('wsgi.url_scheme', 'http'),
                'server': sv
            }
            st = [200]; rh = [[]]; bp = []; sd = [False]
            async def r(): return {'type': 'http.request', 'body': b, 'more_body': False}
            async def se(msg):
                if msg['type'] == 'http.response.start':
                    st[0] = msg['status']
                    rh[0] = [(k.decode(), v.decode()) for k, v in msg.get('headers', [])]
                    sd[0] = True
                elif msg['type'] == 'http.response.body':
                    bp.append(msg.get('body', b''))
            await self.asgi_app(sc, r, se)
            codes = {200: 'OK', 301: 'Moved', 302: 'Found', 303: 'See Other',
                     400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden',
                     404: 'Not Found', 422: 'Unprocessable', 500: 'Server Error'}
            s(str(st[0]) + ' ' + codes.get(st[0], 'OK'), rh[0])
            return [b''.join(bp)]

    application = ASGItoWSGI(_asgi_app)

logger.info("WSGI application ready")

import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
WSGI_PATH = f"/var/www/{USERNAME.lower()}_pythonanywhere_com_wsgi.py"
URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{WSGI_PATH}"

HEADERS = {"Authorization": f"Token {API_TOKEN}"}

WSGI_CONTENT = """import sys
import os
import asyncio

project_home = '/home/JHFGUF/jobhunt'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require'
os.environ['DISABLE_WAL'] = '1'
os.environ['NFS_MODE'] = '1'
os.environ['PYTHONANYWHERE_SITE'] = 'jhfguf.pythonanywhere.com'
os.environ['DISABLE_BACKGROUND_LOOPS'] = 'true'
os.environ['SKIP_INSTALL'] = '1'
os.environ['ADMIN_EMAIL'] = 'samatou683@gmail.com,samsalameh.cv@gmail.com'

from web.app_v2 import app

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

def application(environ, start_response):
    status_code = 200
    headers = []
    body_chunks = []

    content_length = int(environ.get('CONTENT_LENGTH', 0) or 0)
    body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''

    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': environ.get('SERVER_PROTOCOL', 'HTTP/1.1').split('/')[-1],
        'method': environ.get('REQUEST_METHOD', 'GET'),
        'path': environ.get('PATH_INFO', '/'),
        'raw_path': environ.get('PATH_INFO', '/').encode('latin1'),
        'query_string': environ.get('QUERY_STRING', '').encode('latin1'),
        'headers': [(k.lower().replace('http_', '').replace('_', '-').encode('latin1'), v.encode('latin1')) for k, v in environ.items() if k.startswith('HTTP_') or k in ('CONTENT_TYPE', 'CONTENT_LENGTH')],
        'client': (environ.get('REMOTE_ADDR', '127.0.0.1'), int(environ.get('REMOTE_PORT', 0) or 0)),
        'server': (environ.get('SERVER_NAME', 'localhost'), int(environ.get('SERVER_PORT', 80) or 80)),
    }

    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}

    async def send(message):
        nonlocal status_code, headers, body_chunks
        if message['type'] == 'http.response.start':
            status_code = message['status']
            headers = [(k.decode('latin1'), v.decode('latin1')) for k, v in message.get('headers', [])]
        elif message['type'] == 'http.response.body':
            body_chunks.append(message.get('body', b''))

    try:
        _loop.run_until_complete(app(scope, receive, send))
    except Exception as e:
        status_code = 500
        headers = [('Content-Type', 'text/plain')]
        body_chunks = [f"Internal Server Error: {e}".encode('utf-8')]

    status_text = "OK" if status_code == 200 else ("Found" if status_code in (301, 302, 307) else "Status")
    start_response(f"{status_code} {status_text}", headers)
    return body_chunks
"""

def update_wsgi():
    print("Updating WSGI configuration with persistent event loop on PythonAnywhere...")
    r = requests.post(URL, headers=HEADERS, files={"content": WSGI_CONTENT.encode("utf-8")})
    print(f"WSGI Update Status: {r.status_code}")
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/jhfguf.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"Reload status: {r_reload.status_code}")

if __name__ == "__main__":
    update_wsgi()

#!/usr/bin/env python3
"""Upload minified local assets + DEPLOY.md to PythonAnywhere, then reload.

Uses only stdlib (urllib) to avoid requests dependency issues.
Multipart form-data upload matching PA files API expectations.
"""
import os
import uuid
import urllib.request
import urllib.error

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
DOMAIN = 'jhfguf.pythonanywhere.com'
BASE = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}"
headers = {'Authorization': f'Token {PA_TOKEN}'}

FILES = [
    'web/static/js/cyberpunk.js',
    'web/static/js/global-animations.js',
    'web/static/js/i18n.js',
    'web/static/css/index-rtl.css',
    'web/static/css/premium-ui-rtl.css',
    'DEPLOY.md',
]


def multipart_upload(url: str, file_path: str):
    boundary = uuid.uuid4().hex
    with open(file_path, 'rb') as fh:
        file_data = fh.read()
    filename = os.path.basename(file_path)
    body = b''
    body += f'--{boundary}\r\n'.encode()
    body += (f'Content-Disposition: form-data; name="content"; '
             f'filename="{filename}"\r\n').encode()
    body += b'Content-Type: application/octet-stream\r\n\r\n'
    body += file_data
    body += b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    h = dict(headers)
    h['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    req = urllib.request.Request(url, data=body, headers=h, method='POST')
    return urllib.request.urlopen(req, timeout=90)


def main():
    for f in FILES:
        if not os.path.exists(f):
            print(f"SKIP {f} (not found locally)")
            continue
        remote = f"/home/JHFGUF/jobhunt/{f}"
        url = f"{BASE}/files/path{remote}"
        try:
            resp = multipart_upload(url, f)
            print(f"OK   {f} -> {remote} [{resp.status}]")
        except urllib.error.HTTPError as e:
            print(f"ERR  {f}: {e.code} {e.read().decode()[:300]}")
        except Exception as e:  # noqa: BLE001
            print(f"ERR  {f}: {type(e).__name__}: {e}")

    # Reload webapp
    url = f"{BASE}/webapps/{DOMAIN}/reload/"
    try:
        req = urllib.request.Request(url, data=b'', headers=headers, method='POST')
        resp = urllib.request.urlopen(req, timeout=60)
        print(f"RELOAD OK [{resp.status}]")
    except urllib.error.HTTPError as e:
        print(f"RELOAD ERR: {e.code} {e.read().decode()[:300]}")
    except Exception as e:  # noqa: BLE001
        print(f"RELOAD ERR: {type(e).__name__}: {e}")


if __name__ == '__main__':
    main()

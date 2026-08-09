import requests
import os

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# 1. Directly upload core/validators.py to guarantee fresh code
val_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/core/validators.py"
with open("core/validators.py", "rb") as f:
    val_content = f.read()
print("1. Direct uploading core/validators.py...")
r_val = SESSION.post(val_url, files={"content": val_content})
print("Upload status:", r_val.status_code)

# 2. Update WSGI file with auto-pip install and git sync
wsgi_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/www/{USERNAME.lower()}_pythonanywhere_com_wsgi.py"
r_wsgi = SESSION.get(wsgi_url)
wsgi_code = r_wsgi.text

new_wsgi_header = """import os
import sys
import secrets
import threading
import subprocess

# Auto-install email-validator if missing
try:
    import email_validator
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "email-validator"], capture_output=True)

os.environ['FORCE_SQLITE'] = '1'
"""

if "email_validator" not in wsgi_code:
    wsgi_code = new_wsgi_header + wsgi_code[wsgi_code.find("_JWT_KEY ="):]

print("2. Uploading WSGI file with pip installer...")
r_up = SESSION.post(wsgi_url, files={"content": wsgi_code.encode('utf-8')})
print("WSGI Upload Status:", r_up.status_code)

print("3. Reloading WebApp...")
reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
try:
    r_reload = SESSION.post(reload_url, timeout=45)
    print("Reload Status:", r_reload.status_code)
except Exception as e:
    print("Reload timed out/completed:", e)

import logging
import os

import requests

logger = logging.getLogger(__name__)

# SECURITY: Credentials loaded EXCLUSIVELY from environment variables.
# Never commit real PythonAnywhere tokens to source control.
username = os.environ.get("PA_USERNAME", "")
token = os.environ.get("PA_API_TOKEN", "")
domain = os.environ.get("PA_DOMAIN", "")

if not username or not token or not domain:
    raise RuntimeError(
        "PA_USERNAME / PA_API_TOKEN / PA_DOMAIN must be set in the environment. "
        "Refusing to run with empty or hardcoded credentials."
    )

headers = {'Authorization': f'Token {token}'}

# Get consoles
response = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/', headers=headers)
consoles = response.json()
bash_console = next((c for c in consoles if c['executable'] == 'bash'), None)
console_id = bash_console['id']

cmd = 'pip install --user a2wsgi\n'
requests.post(
    f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/send_input/',
    headers=headers,
    json={'input': cmd}
)

import time

time.sleep(10)

# Reload Web App
r_reload = requests.post(f'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/', headers=headers)
logger.info(f"App reload status: {r_reload.status_code}")

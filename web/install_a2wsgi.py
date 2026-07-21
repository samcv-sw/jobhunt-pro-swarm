import logging

import requests

logger = logging.getLogger(__name__)

username = "JHFGUF"
token = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
domain = "jhfguf.pythonanywhere.com"
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

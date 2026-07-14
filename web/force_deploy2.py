import logging

import requests

logger = logging.getLogger(__name__)
import time

username = "JHFGUF"
token = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
domain = "jhfguf.pythonanywhere.com"

headers = {'Authorization': f'Token {token}'}

# Get consoles
response = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/', headers=headers)
consoles = response.json()
bash_console = next((c for c in consoles if c['executable'] == 'bash'), None)
if not bash_console:
    logger.info("No bash console found!")
    exit(1)

console_id = bash_console['id']
logger.info(f"Using console ID: {console_id}")

# Send reset command FOR BOTH possible folders!
cmd = 'cd ~/jobhunt && git fetch origin && git reset --hard origin/main && git clean -fd\n'
requests.post(
    f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/send_input/',
    headers=headers,
    json={'input': cmd}
)
logger.info("Sent git reset command.")

time.sleep(5) # wait for fetch and reset to finish

# Reload Web App
reload_res = requests.post(f'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/', headers=headers)
if reload_res.status_code == 200:
    logger.info("Web app reloaded successfully.")
else:
    logger.info(f"Failed to reload web app: {reload_res.text}")

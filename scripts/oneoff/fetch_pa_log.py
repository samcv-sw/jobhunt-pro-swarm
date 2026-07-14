import os

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')

url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/log/jhfguf.pythonanywhere.com.error.log'
headers = {'Authorization': f'Token {PA_TOKEN}'}

resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    lines = resp.text.split('\n')
    logger.debug('\n'.join(lines[-200:]))
else:
    logger.debug(f'Error fetching log: {resp.status_code} - {resp.text}')

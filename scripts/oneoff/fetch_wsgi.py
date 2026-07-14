import os

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')

url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/www/jhfguf_pythonanywhere_com_wsgi.py'
headers = {'Authorization': f'Token {PA_TOKEN}'}

resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    logger.debug(resp.text)
else:
    logger.debug(f'Error: {resp.status_code} - {resp.text}')

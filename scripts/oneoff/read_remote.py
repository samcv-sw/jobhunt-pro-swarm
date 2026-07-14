import os

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/home/JHFGUF/jobhunt/web/app_v2.py'
resp = requests.get(url, headers={'Authorization': f'Token {PA_TOKEN}'})
logger.debug(resp.text[:200])

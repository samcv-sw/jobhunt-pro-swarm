import os

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/www/jhfguf_pythonanywhere_com_wsgi.py'

wsgi_code = '''import os
import sys

# Auto update from Github on load
try:
    os.system("cd /home/JHFGUF/jobhunt && git fetch origin && git reset --hard FETCH_HEAD")
except Exception:
    pass

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [wsgi_pa] %(message)s")
logger = logging.getLogger("wsgi_pa")

PROJECT = '/home/JHFGUF/jobhunt'
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from web.app_v2 import wsgi_app as application
'''

resp = requests.post(url, headers={'Authorization': f'Token {PA_TOKEN}'}, files={'content': ('wsgi.py', wsgi_code)})
logger.debug(f'WSGI Update: {resp.status_code}')

logger.debug('Reloading...')
DOMAIN = os.environ.get('PA_DOMAIN', 'jhfguf.pythonanywhere.com')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
requests.post(url, headers={'Authorization': f'Token {PA_TOKEN}'})
logger.debug('Done!')

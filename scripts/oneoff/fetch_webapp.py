import json
import os

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/'
headers = {'Authorization': f'Token {PA_TOKEN}'}
resp = requests.get(url, headers=headers)
logger.debug(json.dumps(resp.json(), indent=2))

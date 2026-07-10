import os, requests
PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/www/jhfguf_pythonanywhere_com_wsgi.py'
resp = requests.get(url, headers={'Authorization': f'Token {PA_TOKEN}'})
logger.debug(resp.text)

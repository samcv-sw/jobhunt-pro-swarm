import os, requests
PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
DOMAIN = os.environ.get('PA_DOMAIN', 'jhfguf.pythonanywhere.com')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
requests.post(url, headers={'Authorization': f'Token {PA_TOKEN}'})
print('Reloaded!')

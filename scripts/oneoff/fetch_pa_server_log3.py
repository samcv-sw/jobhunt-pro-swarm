import os, requests
PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')

url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/log/jhfguf.pythonanywhere.com.server.log'
headers = {'Authorization': f'Token {PA_TOKEN}'}

resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    lines = resp.text.split('\n')
    logger.debug('\n'.join(lines[-30:]))
else:
    logger.debug(f'Error fetching server log: {resp.status_code} - {resp.text}')

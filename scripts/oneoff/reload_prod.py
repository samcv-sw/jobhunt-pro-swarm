import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
domain = 'jhfguf.pythonanywhere.com'

headers = {'Authorization': f'Token {PA_TOKEN}'}
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{domain}/reload/'
response = requests.post(url, headers=headers)
if response.status_code == 200:
    logger.debug('Server reloaded successfully.')
else:
    logger.debug(f'Failed to reload: {response.status_code} - {response.text}')

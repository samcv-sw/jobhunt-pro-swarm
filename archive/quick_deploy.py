import os

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
DOMAIN = os.environ.get('PA_DOMAIN', 'jhfguf.pythonanywhere.com')

files_to_upload = ['web/app_v2.py', 'web/routers/campaigns.py', 'web/routers/payments.py']

for f in files_to_upload:
    remote_path = '/home/' + PA_USER.upper() + '/jobhunt/' + f
    url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}'
    headers = {'Authorization': f'Token {PA_TOKEN}'}
    with open(f, 'rb') as file_data:
        resp = requests.post(url, headers=headers, files={'content': file_data})
        print(f'Uploaded {f}: {resp.status_code}')

print('Reloading webapp...')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
requests.post(url, headers={'Authorization': f'Token {PA_TOKEN}'})
print('Done!')

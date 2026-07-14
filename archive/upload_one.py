import os
import time

import requests

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
DOMAIN = os.environ.get('PA_DOMAIN', 'jhfguf.pythonanywhere.com')

f = 'web/app_v2.py'
remote_path = '/home/' + PA_USER.upper() + '/jobhunt/' + f
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}'
headers = {'Authorization': f'Token {PA_TOKEN}'}

while True:
    with open(f, 'rb') as file_data:
        resp = requests.post(url, headers=headers, files={'content': file_data})
    if resp.status_code == 429:
        print(f'Throttled. Retrying in 10s...')
        time.sleep(10)
    else:
        print(f'Uploaded: {resp.status_code}')
        break

print('Reloading...')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
requests.post(url, headers={'Authorization': f'Token {PA_TOKEN}'})
print('Done!')

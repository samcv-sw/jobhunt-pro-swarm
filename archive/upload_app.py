import os

import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
DOMAIN = 'jhfguf.pythonanywhere.com'
headers = {'Authorization': f'Token {PA_TOKEN}'}

f = 'web/app_v2.py'
remote_path = f"/home/JHFGUF/jobhunt/{f}"
url = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}"

with open(f, 'rb') as file_data:
    resp = requests.post(url, headers=headers, files={'content': file_data})
    if resp.status_code in (200, 201):
        print(f"Uploaded {f} successfully.")
    else:
        print(f"Failed {f}: {resp.status_code} - {resp.text}")
        
print('Reloading...')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
resp = requests.post(url, headers=headers)
if resp.status_code == 200:
    print('Server reloaded successfully.')
else:
    print('Failed to reload server:', resp.status_code, resp.text)

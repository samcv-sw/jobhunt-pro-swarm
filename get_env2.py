import os
import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'

url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/home/{PA_USER}/jobhunt/.env'
headers = {'Authorization': f'Token {PA_TOKEN}'}
resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    for line in resp.text.split('\n'):
        if 'TURNSTILE' in line:
            print(line.strip())
else:
    print(f'Failed to get .env: {resp.status_code}')

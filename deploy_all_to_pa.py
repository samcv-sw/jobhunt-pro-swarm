import os
import requests
import time

PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
DOMAIN = os.environ.get('PA_DOMAIN', 'jhfguf.pythonanywhere.com')

if not PA_TOKEN:
    print('PA_TOKEN is not set')
    exit(1)

TARGETS = ['core', 'web/templates', 'web/static', 'web/routers', 'web/app_v2.py']
files_to_upload = []

for target in TARGETS:
    if os.path.isfile(target):
        files_to_upload.append(target)
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            for f in files:
                files_to_upload.append(os.path.join(root, f).replace('\\\\', '/'))

def upload_file(local_path):
    remote_path = '/home/' + PA_USER.upper() + '/jobhunt/' + local_path
    url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}'
    headers = {'Authorization': f'Token {PA_TOKEN}'}
    
    for attempt in range(5):
        with open(local_path, 'rb') as f:
            resp = requests.post(url, headers=headers, files={'content': f})
        
        if resp.status_code in [200, 201]:
            print(f'Uploaded: {local_path}')
            return True
        elif resp.status_code == 429:
            print(f'Throttled on {local_path}. Sleeping 10s...')
            time.sleep(10)
        else:
            print(f'Failed {local_path}: {resp.status_code} - {resp.text}')
            return False
    return False

print(f'Uploading {len(files_to_upload)} files sequentially...')
success = True
for f in files_to_upload:
    if not upload_file(f):
        success = False
        break
    time.sleep(0.5)

if not success:
    print('Deployment failed')
    exit(1)

print('Reloading webapp...')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
headers = {'Authorization': f'Token {PA_TOKEN}'}
resp = requests.post(url, headers=headers)
if resp.status_code == 200:
    print('Webapp reloaded successfully!')
else:
    print(f'Failed to reload: {resp.status_code} - {resp.text}')
    exit(1)

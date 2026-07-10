import os, sys, requests, time

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
DOMAIN = 'jhfguf.pythonanywhere.com'
headers = {'Authorization': f'Token {PA_TOKEN}'}

files_to_upload = [
    'web/app_v2.py',
    'web/templates/dashboard_v3.html',
    'web/templates/en/dashboard_v3.html',
    'web/templates/contact.html',
    'web/templates/en/contact.html',
    'core/revive_campaigns.py'
]

for f in files_to_upload:
    if not os.path.exists(f):
        logger.debug(f"File {f} not found locally.")
        continue
        
    remote_path = f"/home/JHFGUF/jobhunt/{f}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}"
    
    with open(f, 'rb') as file_data:
        resp = requests.post(url, headers=headers, files={'content': file_data})
        if resp.status_code in (200, 201):
            logger.debug(f"Uploaded {f} successfully.")
        else:
            logger.debug(f"Failed {f}: {resp.status_code} - {resp.text}")
            
logger.debug('Reloading...')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
resp = requests.post(url, headers=headers)
if resp.status_code == 200:
    logger.debug('Server reloaded successfully.')
else:
    logger.debug('Failed to reload server.')

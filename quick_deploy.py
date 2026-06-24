import requests, os

PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
USERNAME = 'JHFGUF'
headers = {'Authorization': f'Token {PA_TOKEN}'}
base = r'C:\Users\samde\Desktop\cv sam new ma3 kimi'

# Critical files to deploy (dedup fix + smart-tick)
deploy = [
    (r'core\campaign_runner.py', '/home/JHFGUF/jobhunt/core/campaign_runner.py'),
    (r'core\pa_job_scraper.py', '/home/JHFGUF/jobhunt/core/pa_job_scraper.py'),
]

for local_rel, remote in deploy:
    local_full = os.path.join(base, local_rel)
    if not os.path.exists(local_full):
        print(f'MISSING: {local_rel}')
        continue
    with open(local_full, 'rb') as f:
        content = f.read()
    url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote}'
    resp = requests.post(url, headers=headers, files={'content': content})
    print(f'{local_rel} ({len(content)}B): {resp.status_code}')

# Reload
url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/jhfguf.pythonanywhere.com/reload/'
resp = requests.post(url, headers=headers)
print(f'Reload: {resp.status_code} - {resp.text[:100]}')

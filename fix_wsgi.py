import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/www/jhfguf_pythonanywhere_com_wsgi.py'

headers = {'Authorization': f'Token {PA_TOKEN}'}

# Get current WSGI
resp = requests.get(url, headers=headers)
if resp.status_code != 200:
    print("Failed to get WSGI:", resp.status_code)
    exit(1)

content = resp.text

# Remove the git fetch part
import re
new_content = re.sub(r'try:\s*os\.system\("cd[^"]+git fetch[^"]+"\)\s*except Exception:\s*pass', '', content)

if new_content != content:
    print("Uploading new WSGI without git fetch...")
    resp = requests.post(url, headers=headers, files={'content': new_content})
    print("Status:", resp.status_code)
    
    # Reload server
    reload_url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/jhfguf.pythonanywhere.com/reload/'
    resp = requests.post(reload_url, headers=headers)
    print("Reload Status:", resp.status_code)
else:
    print("No git fetch found in WSGI!")

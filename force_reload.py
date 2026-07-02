import os, requests
PA_USER = os.environ.get('PA_USER', 'jhfguf').lower()
PA_TOKEN = os.environ.get('PA_TOKEN')
domain = "jhfguf.pythonanywhere.com"

url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{domain}/reload/'
headers = {'Authorization': f'Token {PA_TOKEN}'}

resp = requests.post(url, headers=headers)
print(f"Reload status: {resp.status_code}")
print(resp.text)

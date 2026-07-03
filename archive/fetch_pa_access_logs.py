import os
import requests
from dotenv import load_dotenv

load_dotenv()

PA_USER = 'JHFGUF'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'

headers = {'Authorization': f'Token {PA_TOKEN}'}

# Access log path
log_url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/var/log/jhfguf.pythonanywhere.com.access.log'

print("Fetching PythonAnywhere access logs...")
r = requests.get(log_url, headers=headers)
if r.status_code == 200:
    lines = r.text.splitlines()[-100:]
    print("=== TAIL OF ACCESS LOG ===")
    for l in lines:
        print(l)
else:
    print(f"Failed to fetch access logs: {r.status_code} - {r.text}")

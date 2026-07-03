import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

PA_USER = 'JHFGUF'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'

headers = {'Authorization': f'Token {PA_TOKEN}'}

print("Fetching PythonAnywhere Always-On tasks...")
r_always_on = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/always_on/', headers=headers)
if r_always_on.status_code == 200:
    print("Always-On Tasks:")
    print(json.dumps(r_always_on.json(), indent=2))
else:
    print(f"Failed to fetch Always-On tasks: {r_always_on.status_code} - {r_always_on.text}")

print("\nFetching PythonAnywhere Scheduled tasks...")
r_scheduled = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/schedule/', headers=headers)
if r_scheduled.status_code == 200:
    print("Scheduled Tasks:")
    print(json.dumps(r_scheduled.json(), indent=2))
else:
    print(f"Failed to fetch Scheduled tasks: {r_scheduled.status_code} - {r_scheduled.text}")

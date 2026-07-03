import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

PA_USER = 'JHFGUF'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'

headers = {'Authorization': f'Token {PA_TOKEN}'}

print("Fetching PythonAnywhere account info...")
# Try checking cpu usage endpoint or webapps endpoint
r = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/cpu/', headers=headers)
if r.status_code == 200:
    print("CPU Info:")
    print(json.dumps(r.json(), indent=2))
else:
    print(f"Failed to fetch CPU info: {r.status_code} - {r.text}")

r_web = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/', headers=headers)
if r_web.status_code == 200:
    print("\nWebapps:")
    print(json.dumps(r_web.json(), indent=2))
else:
    print(f"Failed to fetch webapps: {r_web.status_code} - {r_web.text}")

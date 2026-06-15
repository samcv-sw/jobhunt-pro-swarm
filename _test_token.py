"""Test PA API token against all endpoints"""
import requests

TOKEN = '34fe3a4cafefe3a4ac8d592119d5480a0b988971'
h = {'Authorization': f'Token {TOKEN}'}
USER = 'JHFGUF'
BASE = 'https://www.pythonanywhere.com/api/v0'

endpoints = [
    f'{BASE}/user/{USER}/',
    f'{BASE}/user/{USER}/webapps/',
    f'{BASE}/user/{USER}/consoles/',
    f'{BASE}/user/{USER}/cpu/',
    f'{BASE}/user/{USER}/files/?path=/home/{USER}',
]

for url in endpoints:
    try:
        r = requests.get(url, headers=h, timeout=15)
        short = url.replace(BASE, '')
        print(f'{r.status_code} {short}')
        if r.status_code == 200:
            print(f'  OK! {r.text[:200]}')
        elif r.status_code == 401:
            print(f'  UNAUTHORIZED')
    except Exception as e:
        print(f'ERR {short}: {e}')

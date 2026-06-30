import requests
import time

TOKEN = '874997673d6b9787dc4e3a938dd45a1930f1c85c'
USERNAME = 'JHFGUF'
headers = {'Authorization': f'Token {TOKEN}'}

console_url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/'
res = requests.post(console_url, headers=headers, json={'executable': 'bash'})
console_id = res.json()['id']

cmd = """python -c "
import sqlite3
conn = sqlite3.connect('/home/JHFGUF/jobhunt/jobhunt_saas_v2.db')
print('Emails:', [r[0] for r in conn.execute('SELECT email FROM users').fetchall()])
"
"""

requests.post(f'{console_url}{console_id}/send_input/', headers=headers, json={'input': cmd + '\n'})
time.sleep(3)

out_res = requests.get(f'{console_url}{console_id}/get_latest_output/', headers=headers)
print('Remote Output:', out_res.json().get('output', ''))

requests.delete(f'{console_url}{console_id}/', headers=headers)

import requests
import urllib3

urllib3.disable_warnings()
TOKEN='874997673d6b9787dc4e3a938dd45a1930f1c85c'
BASE='https://www.pythonanywhere.com/api/v0/user/JHFGUF'
headers={'Authorization':f'Token {TOKEN}'}

# Get existing consoles
r = requests.get(f'{BASE}/consoles/', headers=headers, verify=False)
consoles = r.json()

if consoles:
    print(f"Found {len(consoles)} consoles. Deleting console {consoles[0]['id']} to make room...")
    requests.delete(f'{BASE}/consoles/{consoles[0]["id"]}/', headers=headers, verify=False)

# Create new console
r = requests.post(f'{BASE}/consoles/', headers=headers, json={'executable': 'bash'}, verify=False)
if r.status_code in (200, 201):
    console_id = r.json()['id']
    cmd = 'cd ~/jobhunt && source venv/bin/activate && python core/queue_worker.py\n'
    requests.post(f'{BASE}/consoles/{console_id}/send_input/', headers=headers, json={'input': cmd}, verify=False)
    print(f'Started queue worker perfectly in new console {console_id}!')
else:
    print(f'Failed to create console: {r.text}')

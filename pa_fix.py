import requests
import time
token = '1181b0064725fc1bb9f3043c19f943780eeebd3b'
headers = {'Authorization': f'Token {token}'}
base_url = 'https://www.pythonanywhere.com/api/v0/user/JHFGUF'

resp = requests.get(f'{base_url}/consoles/', headers=headers)
if resp.status_code == 200:
    for c in resp.json():
        print('Deleting console', c['id'])
        requests.delete(f"{base_url}/consoles/{c['id']}/", headers=headers)

resp = requests.post(f'{base_url}/consoles/', headers=headers, json={'executable': 'bash'})
if resp.status_code == 201:
    console_id = resp.json()['id']
    print('New Console ID:', console_id)
    time.sleep(2)
    cmd = 'cd jobhunt && git pull origin main && touch /var/www/jhfguf_pythonanywhere_com_wsgi.py\n'
    requests.post(f'{base_url}/consoles/{console_id}/send_input/', headers=headers, json={'input': cmd})
    time.sleep(10)
    out = requests.get(f'{base_url}/consoles/{console_id}/get_latest_output/', headers=headers)
    print(out.json().get('output', ''))
else:
    print('Failed to start console:', resp.status_code, resp.text)

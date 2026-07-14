import time

import requests

username = "JHFGUF"
token = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
domain = "jhfguf.pythonanywhere.com"

headers = {'Authorization': f'Token {token}'}

response = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/', headers=headers)
consoles = response.json()
bash_console = next((c for c in consoles if c['executable'] == 'bash'), None)
console_id = bash_console['id']

cmd = 'cd ~/jobhunt && git log -n 3 --oneline\n'
requests.post(
    f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/send_input/',
    headers=headers,
    json={'input': cmd}
)
time.sleep(2)
output_res = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/get_latest_output/', headers=headers)
print("Console output:")
print(output_res.json().get('output', ''))

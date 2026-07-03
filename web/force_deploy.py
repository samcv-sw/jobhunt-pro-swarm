import requests
import time

username = "JHFGUF"
token = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
domain = "jhfguf.pythonanywhere.com"

headers = {'Authorization': f'Token {token}'}

# Create a new bash console to get clean output
create_res = requests.post(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/', headers=headers, json={'executable': 'bash'})
if create_res.status_code not in [200, 201]:
    print("Failed to create console", create_res.text)
    exit(1)

bash_console = create_res.json()
console_id = bash_console['id']
print(f"Using console ID: {console_id}")

time.sleep(2) # wait for console to start

# Send reset command FOR BOTH possible folders!
cmd = 'cd ~/jobhunt && git fetch origin && git reset --hard origin/main && git clean -fd\n'
requests.post(
    f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/send_input/',
    headers=headers,
    json={'input': cmd}
)
print("Sent git reset command.")

time.sleep(5) # wait for fetch and reset to finish

# Get console output
output_res = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/get_latest_output/', headers=headers)
print("Console output:")
print(output_res.json().get('output', ''))

# Reload Web App
reload_res = requests.post(f'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/', headers=headers)
if reload_res.status_code == 200:
    print("Web app reloaded successfully.")
else:
    print(f"Failed to reload web app: {reload_res.text}")

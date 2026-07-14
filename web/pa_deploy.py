import time

import requests

username = "JHFGUF"
token = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
domain = "jhfguf.pythonanywhere.com"

headers = {'Authorization': f'Token {token}'}

# 1. Get consoles
response = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/', headers=headers)
if response.status_code == 200:
    consoles = response.json()
    bash_console = next((c for c in consoles if c['executable'] == 'bash'), None)

    if not bash_console:
        # Create a new bash console
        create_res = requests.post(f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/', headers=headers, json={'executable': 'bash'})
        bash_console = create_res.json()
        time.sleep(2) # wait for console to start

    console_id = bash_console['id']
    logger.debug(f"Using console ID: {console_id}")

    # 2. Send git pull command
    cmd = 'cd ~/jobhunt && git pull origin main\n'
    requests.post(
        f'https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/send_input/',
        headers=headers,
        json={'input': cmd}
    )
    logger.debug("Sent git pull command.")

    time.sleep(5) # wait for pull to finish

    # 3. Reload Web App
    reload_res = requests.post(f'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/', headers=headers)
    if reload_res.status_code == 200:
        logger.debug("Web app reloaded successfully.")
    else:
        logger.debug(f"Failed to reload web app: {reload_res.text}")
else:
    logger.debug(f"Failed to fetch consoles: {response.text}")

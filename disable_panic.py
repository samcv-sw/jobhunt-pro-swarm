import requests

TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
CONSOLE_ID = "47334258"

url = f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/consoles/{CONSOLE_ID}/send_input/"
headers = {"Authorization": f"Token {TOKEN}"}

# Send the command to remove the panic mode cache file
data = {"input": "rm /home/JHFGUF/jobhunt/cache/panic_state.json\n"}
r1 = requests.post(url, headers=headers, json=data)
print(f"Delete state: {r1.status_code}")

# Reload the web app so it resets
reload_url = "https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/reload/"
r2 = requests.post(reload_url, headers=headers)
print(f"Reload app: {r2.status_code}")

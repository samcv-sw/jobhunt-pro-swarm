import requests

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
USERNAME = "jhfguf"
headers = {"Authorization": f"Token {PA_TOKEN}"}

log_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/log/jhfguf.pythonanywhere.com.error.log"
resp = requests.get(log_url, headers=headers)
if resp.status_code == 200:
    with open("_pa_error.log", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Successfully wrote error log to _pa_error.log")
else:
    print(f"Failed to fetch error log: {resp.status_code} - {resp.text}")

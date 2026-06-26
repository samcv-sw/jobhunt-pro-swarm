import requests

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
USERNAME = "jhfguf"
headers = {"Authorization": f"Token {PA_TOKEN}"}

log_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/log/jhfguf.pythonanywhere.com.error.log"
resp = requests.get(log_url, headers=headers)
if resp.status_code == 200:
    lines = resp.text.split('\n')
    print("Last 30 lines of error log:")
    for line in lines[-30:]:
        print(line)
else:
    print(f"Failed to fetch error log: {resp.status_code} - {resp.text}")

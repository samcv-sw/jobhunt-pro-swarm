import requests

PA_TOKEN = "34fe3a4cafefe3a4ac8d592119d5480a0b988971"
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

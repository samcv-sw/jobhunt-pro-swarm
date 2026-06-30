import urllib.request
import json

USER = 'JHFGUF'
TOKEN = '874997673d6b9787dc4e3a938dd45a1930f1c85c'
url = f'https://www.pythonanywhere.com/api/v0/user/{USER}/files/path/home/{USER}/jobhunt/jobhunt_saas_v2.db'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Token {TOKEN}')

try:
    with urllib.request.urlopen(req) as response:
        with open('pa_db.sqlite', 'wb') as f:
            f.write(response.read())
    print("Database downloaded successfully!")
except Exception as e:
    print(f"Failed to download: {e}")

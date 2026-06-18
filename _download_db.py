import urllib.request
import os

PA_TOKEN = "874997673d6b9787dc4e3a938dd45a1930f1c85c"
USER = "JHFGUF"
url = f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path/home/JHFGUF/jobhunt/jobhunt_saas_v2.db"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Token {PA_TOKEN}")

print("Downloading database from PythonAnywhere...")
try:
    with urllib.request.urlopen(req) as response, open('pa_jobhunt_saas_v2.db', 'wb') as out_file:
        out_file.write(response.read())
    print("Download complete: pa_jobhunt_saas_v2.db")
except Exception as e:
    print(f"Error: {e}")

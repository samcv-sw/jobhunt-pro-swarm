import requests
import os

TOKEN = "1181b0064725fc1bb9f3043c19f943780eeebd3b"
USERNAME = "JHFGUF"
headers = {"Authorization": f"Token {TOKEN}"}

def upload_file(local_path, remote_path):
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
    with open(local_path, 'rb') as f:
        res = requests.post(url, headers=headers, files={"content": f})
    if res.status_code in (200, 201):
        print(f"Uploaded {local_path} successfully!")
    else:
        print(f"Failed to upload {local_path}: {res.text}")

def reload_webapp():
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/jhfguf.pythonanywhere.com/reload/"
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        print("Webapp reloaded successfully!")
    else:
        print(f"Failed to reload webapp: {res.text}")

upload_file(r"web\templates\index_v3.html", f"/home/{USERNAME}/jobhunt/web/templates/index_v3.html")
reload_webapp()

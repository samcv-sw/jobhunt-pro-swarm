import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

files_to_delete = [
    f"/home/{USERNAME}/jobhunt/var/log/jhfguf.pythonanywhere.com.error.log",
    f"/home/{USERNAME}/jobhunt/var/log/jhfguf.pythonanywhere.com.server.log",
    f"/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db",
    f"/home/{USERNAME}/jobhunt/data/auto_backups",
    f"/home/{USERNAME}/jobhunt/web/__pycache__",
    f"/home/{USERNAME}/jobhunt/core/__pycache__",
    f"/home/{USERNAME}/jobhunt/scripts/__pycache__",
    f"/home/{USERNAME}/jobhunt/routers/__pycache__",
]

for file_path in files_to_delete:
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{file_path}"
    res = SESSION.delete(url)
    print(f"Delete {file_path}: {res.status_code}")

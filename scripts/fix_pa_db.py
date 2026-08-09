import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

# Delete the corrupted SQLite file
DB_PATH = f"/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db"
r_del = requests.delete(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{DB_PATH}", headers=HEADERS)
print("Delete corrupted DB status:", r_del.status_code)

# Reload webapp
r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
print("Reload status:", r_reload.status_code)

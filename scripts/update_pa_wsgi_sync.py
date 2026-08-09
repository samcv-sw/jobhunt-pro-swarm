import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
WSGI_PATH = f"/var/www/{USERNAME.lower()}_pythonanywhere_com_wsgi.py"
URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{WSGI_PATH}"

HEADERS = {"Authorization": f"Token {API_TOKEN}"}

WSGI_CONTENT = """import sys
import os

project_home = '/home/JHFGUF/jobhunt'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from cloud_wsgi import application
"""

def update_wsgi():
    print("Updating WSGI configuration to import cloud_wsgi (Auto Git Pull + Background Applier)...")
    for attempt in range(3):
        try:
            r = requests.post(URL, headers=HEADERS, files={"content": WSGI_CONTENT.encode("utf-8")}, timeout=15)
            print(f"WSGI File Update Status: {r.status_code}")
            if r.status_code in (200, 201):
                break
        except Exception as e:
            print(f"WSGI upload attempt failed: {e}")
            
    r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
    print(f"Webapp Reload status: {r_reload.status_code}")

if __name__ == "__main__":
    update_wsgi()

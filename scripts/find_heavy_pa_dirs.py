import requests

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def inspect_folder(path):
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/tree/path{path}"
    r = SESSION.get(url)
    if r.status_code == 200:
        files = r.json()
        print(f"Total entries in {path}: {len(files)}")
        # Delete corrupted sqlite DB immediately
        if f"/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db" in files:
            r_del = SESSION.delete(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/data/jobhunt_saas_v2.db")
            print("Deleted malformed DB:", r_del.status_code)
    else:
        print(f"Error inspecting {path}: {r.status_code}")

inspect_folder(f"/home/{USERNAME}/jobhunt/")

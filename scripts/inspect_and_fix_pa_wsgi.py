import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def inspect_wsgi():
    print("=== INSPECTING PYTHONANYWHERE WSGI FILE ===")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/www/jhfguf_pythonanywhere_com_wsgi.py"
    r = SESSION.get(url)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        print("=== /var/www/jhfguf_pythonanywhere_com_wsgi.py Content ===")
        print(r.text)
        print("=======================================================")
    else:
        print(f"Error fetching WSGI file: {r.text}")

if __name__ == "__main__":
    inspect_wsgi()

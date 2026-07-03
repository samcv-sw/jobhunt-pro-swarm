# scratch/read_pa_error_log.py
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

TOKEN = "7e7ad272cc2d4470e8078fca29dfacf301fb01fe"
USERNAME = "JHFGUF"
HEADERS = {
    "Authorization": f"Token {TOKEN}"
}

def get_error_log():
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/log/{USERNAME.lower()}.pythonanywhere.com.error.log"
    print(f"Fetching error log from {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            lines = response.text.splitlines()
            print(f"\nLast 120 lines of PythonAnywhere error log:")
            print("==================================================")
            for line in lines[-120:]:
                print(line)
            print("==================================================")
        else:
            print(f"Failed to fetch error log. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    get_error_log()

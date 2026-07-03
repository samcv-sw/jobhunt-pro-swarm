import requests

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
PA_USER = "JHFGUF"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}"
HEADERS = {
    "Authorization": f"Token {PA_TOKEN}",
}

try:
    error_log_path = f"/var/log/jhfguf.pythonanywhere.com.error.log"
    print(f"Fetching last 300 lines of error log from PA...")
    resp_err = requests.get(f"{BASE_URL}/files/path/{error_log_path}", headers=HEADERS, timeout=20)
    if resp_err.status_code == 200:
        content = resp_err.text
        lines = content.splitlines()
        print(f"Total lines: {len(lines)}")
        for line in lines[-300:]:
            # Clean non-ascii characters to avoid encoding issues on Windows console
            clean_line = line.encode('ascii', 'ignore').decode('ascii')
            print(clean_line)
    else:
        print(f"Could not fetch error log: {resp_err.status_code} - {resp_err.text}")
except Exception as e:
    print("Error:", e)

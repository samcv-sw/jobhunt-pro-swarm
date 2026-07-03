import requests

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
PA_USER = "JHFGUF"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}"
HEADERS = {
    "Authorization": f"Token {PA_TOKEN}",
}

try:
    # 1. List webapps
    resp = requests.get(f"{BASE_URL}/webapps/", headers=HEADERS, timeout=15)
    print("=== PA WEBAPPS ===")
    if resp.status_code == 200:
        webapps = resp.json()
        print("Raw Webapps Response:", webapps)
    else:
        print(f"Failed to list webapps: {resp.status_code} - {resp.text}")
        
    # 2. Reload the webapp
    print("\n=== RELOADING WEBAPP ===")
    # The reload endpoint can be webapps/jhfguf.pythonanywhere.com/reload/ or webapps/{id}/reload/
    # Let's try both to be absolutely sure!
    reload_url1 = f"{BASE_URL}/webapps/jhfguf.pythonanywhere.com/reload/"
    resp_reload1 = requests.post(reload_url1, headers=HEADERS, timeout=30)
    print(f"Reload by domain Status: {resp_reload1.status_code}")
    if resp_reload1.status_code not in (200, 204):
        print(f"  Domain reload failed: {resp_reload1.text}")
        
    # 3. Read the error log
    print("\n=== LIVE ERROR LOG ===")
    error_log_path = f"/var/log/jhfguf.pythonanywhere.com.error.log"
    print(f"Reading live error log from PA: {error_log_path}")
    resp_err = requests.get(f"{BASE_URL}/files/path/{error_log_path}", headers=HEADERS, timeout=20)
    if resp_err.status_code == 200:
        content = resp_err.text
        lines = content.splitlines()
        print(f"Last 50 lines of live error log:")
        for line in lines[-50:]:
            print(f"  {line}")
    else:
        print(f"Could not fetch error log: {resp_err.status_code} - {resp_err.text}")

except Exception as e:
    print("Error querying PA webapp API:", e)

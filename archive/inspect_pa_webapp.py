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
        for w in webapps:
            print(f"Domain: {w['domain_name']} | ID: {w['id']} | Python: {w['python_version']} | Active: {w['active']}")
            # Detailed config
            print(f"  Virtualenv: {w.get('virtualenv_path')}")
            print(f"  Force HTTPS: {w.get('force_https')}")
    else:
        print(f"Failed to list webapps: {resp.status_code} - {resp.text}")
        
    # 2. Reload the webapp
    print("\n=== RELOADING WEBAPP ===")
    reload_url = f"{BASE_URL}/webapps/jhfguf.pythonanywhere.com/reload/"
    resp_reload = requests.post(reload_url, headers=HEADERS, timeout=30)
    print(f"Reload Status: {resp_reload.status_code}")
    if resp_reload.status_code in (200, 204):
        print("Webapp successfully reloaded!")
    else:
        print(f"Reload failed: {resp_reload.text}")

    # 3. Check Webapp Log Files
    print("\n=== LOG FILES ===")
    resp_logs = requests.get(f"{BASE_URL}/files/tree/?path=/home/{PA_USER}/.rmg-logs/", headers=HEADERS, timeout=15)
    # Wait, let's just list the logs directory or standard error log
    # Error log path is usually /var/log/jhfguf.pythonanywhere.com.error.log
    # Let's read the error log file
    error_log_path = f"/var/log/jhfguf.pythonanywhere.com.error.log"
    print(f"Reading live error log from PA: {error_log_path}")
    resp_err = requests.get(f"{BASE_URL}/files/path/{error_log_path}", headers=HEADERS, timeout=20)
    if resp_err.status_code == 200:
        content = resp_err.text
        lines = content.splitlines()
        print(f"Last 30 lines of live error log:")
        for line in lines[-30:]:
            print(f"  {line}")
    else:
        print(f"Could not fetch error log: {resp_err.status_code} - {resp_err.text}")

except Exception as e:
    print("Error querying PA webapp API:", e)

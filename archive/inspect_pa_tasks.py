import requests

PA_TOKEN = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
PA_USER = "JHFGUF"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}"
HEADERS = {
    "Authorization": f"Token {PA_TOKEN}",
}

try:
    # 1. Get user info
    resp = requests.get(f"{BASE_URL}/cpu/", headers=HEADERS, timeout=15)
    print("=== PA ACCOUNT & CPU INFO ===")
    if resp.status_code == 200:
        print(resp.json())
    else:
        print(f"Failed: {resp.status_code} - {resp.text}")
        
    # 2. Get always-on tasks
    resp_ao = requests.get(f"{BASE_URL}/alwayson/", headers=HEADERS, timeout=15)
    print("\n=== ALWAYS-ON TASKS ===")
    if resp_ao.status_code == 200:
        tasks = resp_ao.json()
        print(f"Found {len(tasks)} always-on tasks:")
        for t in tasks:
            print(t)
    else:
        print(f"Failed: {resp_ao.status_code} - {resp_ao.text}")
        
    # 3. Get scheduled tasks (cron)
    resp_sched = requests.get(f"{BASE_URL}/schedule/", headers=HEADERS, timeout=15)
    print("\n=== SCHEDULED TASKS ===")
    if resp_sched.status_code == 200:
        tasks = resp_sched.json()
        print(f"Found {len(tasks)} scheduled tasks:")
        for t in tasks:
            print(t)
    else:
        print(f"Failed: {resp_sched.status_code} - {resp_sched.text}")

except Exception as e:
    print("Error querying PA API:", e)

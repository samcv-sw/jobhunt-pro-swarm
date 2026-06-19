"""Force fresh search + tick"""
import requests, time
h = {"Authorization": "Token 874997673d6b9787dc4e3a938dd45a1930f1c85c"}
BASE = "/home/JHFGUF/jobhunt"

# Clear cache
for fname in ["_search_cache.json", "_li_rot.dat", "_search_rot.dat"]:
    r = requests.delete(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/{fname}", headers=h)
    print(f"DEL {fname}: {r.status_code}")

# Force tick with fresh scrape
r = requests.get("https://jhfguf.pythonanywhere.com/api/cron/tick?timeout=260&reset=cooldown", timeout=300)
print(f"\nTICK: {r.text[:500] if r.text else 'empty'}")

# Check cache
time.sleep(3)
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/_search_cache.json", headers=h, timeout=15)
if r.status_code == 200:
    data = r.json()
    jobs = data.get("jobs", [])
    srcs = set(j.get("source","?") for j in jobs) if jobs else set()
    print(f"\nCache: {len(jobs)} jobs from {srcs}")
else:
    print(f"\nCache: HTTP {r.status_code}")

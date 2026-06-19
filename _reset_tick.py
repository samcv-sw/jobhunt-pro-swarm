"""Reset running campaigns + force tick"""
import requests, sqlite3, time, os
h = {"Authorization": "Token 874997673d6b9787dc4e3a938dd45a1930f1c85c"}
BASE = "/home/JHFGUF/jobhunt"

r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/jobhunt_saas_v2.db", headers=h, timeout=30)
with open("_reset.db","wb") as f: f.write(r.content)
conn = sqlite3.connect("_reset.db")

conn.execute("UPDATE campaigns SET status='pending', started_at=NULL WHERE status='running'")
conn.commit()

cur = conn.execute("SELECT campaign_id, status, sent_count FROM campaigns ORDER BY id")
print("After reset:")
for row in cur.fetchall():
    print(f"  {row[0][:22]:22s} | {row[1]:9s} | {row[2]}")
conn.close()
with open("_reset.db","rb") as f:
    requests.post(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/jobhunt_saas_v2.db", headers=h, files={"content": f})

# TICK!
r = requests.get("https://jhfguf.pythonanywhere.com/api/cron/tick?timeout=260&reset=cooldown&clear_stuck=1", timeout=300)
print(f"\nTICK: {r.text[:500] if r.text else 'empty'}")

# Check cache
time.sleep(3)
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/_search_cache.json", headers=h, timeout=15)
if r.status_code == 200:
    import json
    data = json.loads(r.text)
    jobs = data.get("jobs", [])
    srcs = set(j.get("source","?") for j in jobs) if jobs else set()
    print(f"\nCache: {len(jobs)} jobs from {srcs}")
else:
    print(f"\nCache: HTTP {r.status_code}")

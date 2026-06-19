import requests, json, sqlite3, io, os

TOKEN = "874997673d6b9787dc4e3a938dd45a1930f1c85c"

# Download PA db
url = "https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path/home/JHFGUF/jobhunt/jobhunt_saas_v2.db"
r = requests.get(url, headers={"Authorization": f"Token {TOKEN}"}, timeout=30)

with open("_pa_temp.db", "wb") as f:
    f.write(r.content)

conn = sqlite3.connect("_pa_temp.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check profile
cur.execute("SELECT * FROM cv_profiles")
profiles = [dict(r) for r in cur.fetchall()]
print("=== PROFILES ===")
for p in profiles:
    print(f"  #{p.get('id')}: name='{str(p.get('name',''))[:30]}' email='{str(p.get('email',''))[:30]}' title='{str(p.get('title',''))[:30]}'")

# Check campaigns BEFORE reset
cur.execute("SELECT campaign_id, status, total_jobs, created_at FROM campaigns ORDER BY id")
rows = cur.fetchall()
print(f"\n=== CAMPAIGNS BEFORE ===")
for r in rows:
    d = dict(r)
    print(f"  {d['campaign_id']}: status={d['status']}, jobs={d['total_jobs']}, created={str(d.get('created_at',''))[:16]}")

# Reset failed campaigns with 0 jobs to "pending"
cur.execute("""
    UPDATE campaigns 
    SET status='pending', completed_at=NULL, started_at=NULL 
    WHERE status='failed' AND total_jobs=0
""")
affected = cur.rowcount
conn.commit()
print(f"\n✅ Reset {affected} failed campaigns to pending")

# Verify AFTER
cur.execute("SELECT campaign_id, status, total_jobs FROM campaigns ORDER BY id")
print("=== CAMPAIGNS AFTER ===")
for r in cur.fetchall():
    d = dict(r)
    print(f"  {d['campaign_id']}: status={d['status']}, jobs={d['total_jobs']}")

# Upload the modified db back to PA
print("\nUploading modified DB to PA...")
conn.close()
with open("_pa_temp.db", "rb") as f:
    upload = requests.post(
        url,
        headers={"Authorization": f"Token {TOKEN}"},
        files={"content": f}
    )
    print(f"Upload status: {upload.status_code}")
    if upload.status_code == 200:
        print("✅ DB updated on PA")
    else:
        print(f"Upload response: {upload.text[:200]}")

# Clean up
os.remove("_pa_temp.db")

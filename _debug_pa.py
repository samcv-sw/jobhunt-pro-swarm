"""Add debug endpoint to PA app to test Dice/Wuzzuf scrapers"""
import requests

# Read current app_v2.py
r = requests.get("https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path/home/JHFGUF/jobhunt/web/app_v2.py",
                 headers={"Authorization": "Token 874997673d6b9787dc4e3a938dd45a1930f1c85c"}, timeout=30)

# Check if test endpoint already exists
if "/api/test/scrapers" in r.text:
    print("Test endpoint already exists!")
else:
    print("Need to add test endpoint")
    
# Just try the scrapers directly through an existing endpoint
# Check log for Dice/Wuzzuf errors from last deploy  
r = requests.get("https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path/var/log/jhfguf.pythonanywhere.com.error.log",
                 headers={"Authorization": "Token 874997673d6b9787dc4e3a938dd45a1930f1c85c"}, timeout=30)
log = r.text
# Search for lines around 20:28-20:30 (the deploy tick time)
for line in log.split("\n"):
    if "20:2" in line and ("Dice" in line.lower() or "wuzzuf" in line.lower() or "bayt" in line.lower() or "MEGA" in line.lower() or "import" in line.lower() or "error" in line.lower() or "traceback" in line.lower()):
        # Just print ASCII only
        clean = "".join(c for c in line if ord(c) < 128)
        print(clean[:300])

print("\n--- Last 20 lines with 'skip' or 'failed' ---")
for line in log.split("\n")[-30:]:
    if "skip" in line.lower() or "failed" in line.lower() or "Error" in line:
        clean = "".join(c for c in line if ord(c) < 128)
        print(clean[:300])

import os
import re
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

route_pattern = re.compile(r'@(?:app|router)\.get\([\'"]([^\'"]+)[\'"]')

all_routes = set()

for root, dirs, files in os.walk(WEB_DIR):
    for f in files:
        if f.endswith(".py"):
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                matches = route_pattern.findall(content)
                for m in matches:
                    if "{" not in m and not m.startswith("/api/v"):
                        all_routes.add(m)

sorted_routes = sorted(list(all_routes))
print(f"Total Unique User-Facing GET Pages Found: {len(sorted_routes)}")

categories = {
    "Core Application & Dashboards": [],
    "ATS & Resume Sculptor": [],
    "AI SDR, Outreach & Auto-Applier": [],
    "Analytics & Growth Station": [],
    "Public & Marketing Pages": [],
    "English Pages (/en/*)": [],
    "Arabic Pages (/ar/*)": [],
    "Admin & System Control": []
}

for r in sorted_routes:
    if r.startswith("/en/"):
        categories["English Pages (/en/*)"].append(r)
    elif r.startswith("/ar/"):
        categories["Arabic Pages (/ar/*)"].append(r)
    elif any(k in r for k in ["admin", "emperor", "system", "status"]):
        categories["Admin & System Control"].append(r)
    elif any(k in r for k in ["ats", "resume", "sculptor", "cv", "portfolio"]):
        categories["ATS & Resume Sculptor"].append(r)
    elif any(k in r for k in ["auto-applier", "sdr", "outreach", "blaster", "campaign"]):
        categories["AI SDR, Outreach & Auto-Applier"].append(r)
    elif any(k in r for k in ["analytics", "radar", "growth", "stats", "funnel"]):
        categories["Analytics & Growth Station"].append(r)
    elif any(k in r for k in ["dashboard", "battle", "war", "god", "singularity", "futuristic"]):
        categories["Core Application & Dashboards"].append(r)
    else:
        categories["Public & Marketing Pages"].append(r)

print("\n--- Testing key sample routes against Live Cloud (https://jhfguf.pythonanywhere.com) ---")
test_sample = ["/", "/login", "/register", "/dashboard", "/battle-station", "/user-dashboard", "/ats-scorer", "/sent-emails", "/pricing", "/privacy", "/terms", "/health"]

for route in test_sample:
    url = f"https://jhfguf.pythonanywhere.com{route}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        print(f"[LIVE CHECK] {route:<30} --> HTTP {res.status_code} ({len(res.text)} bytes)")
    except Exception as e:
        print(f"[LIVE CHECK] {route:<30} --> ERROR: {e}")

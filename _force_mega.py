"""Force new search + tick"""
import requests, sqlite3, json, os
h = {"Authorization": "Token 874997673d6b9787dc4e3a938dd45a1930f1c85c"}
BASE = "/home/JHFGUF/jobhunt"

# 1. List cache files
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/", headers=h, timeout=15)
print("Files:", r.status_code)
if r.status_code == 200:
    for f in r.json():
        fpath = f.get("path", f.get("name",""))
        print(f"  {fpath}")

# 2. Clear cache files explicitly
for fname in ["_search_cache.json", "_li_rot.dat", "_search_rot.dat"]:
    r = requests.delete(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path{BASE}/{fname}", headers=h)
    print(f"  DEL {fname}: {r.status_code}")

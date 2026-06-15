#!/usr/bin/env python3
"""Explore PA filesystem with correct token"""
import urllib.request, json

PA_TOKEN = "34fe3a4cafefe3a4ac8d592119d5480a0b988971"
USER = "JHFGUF"
BASE = f"https://www.pythonanywhere.com/api/v0/user/{USER}"

paths_to_try = [
    "/files/path/home/JHFGUF/jobhunt/",
    "/files/path/home/JHFGUF/",
    "/files/path/",
    "/files/tree/",
]

for path in paths_to_try:
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Token {PA_TOKEN}"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        print(f"✅ {path}")
        if isinstance(data, dict):
            for k in list(data.keys())[:5]:
                v = str(data[k])[:200]
                print(f"  {k}: {v}")
        elif isinstance(data, list):
            for item in data[:10]:
                print(f"  {str(item)[:200]}")
        else:
            print(f"  {str(data)[:500]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:100]
        print(f"❌ {path} — {e.code}: {body}")

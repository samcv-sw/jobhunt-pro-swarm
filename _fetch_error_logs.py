#!/usr/bin/env python3
import urllib.request

PA_TOKEN = "874997673d6b9787dc4e3a938dd45a1930f1c85c"
USER = "JHFGUF"
DOMAIN = "jhfguf.pythonanywhere.com"

url = f"https://www.pythonanywhere.com/api/v0/user/{USER}/files/path/var/log/{DOMAIN}.error.log"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Token {PA_TOKEN}")

try:
    resp = urllib.request.urlopen(req)
    content = resp.read().decode('utf-8', errors='replace')
    # Print last 50 lines
    lines = content.strip().split("\n")
    for line in lines[-50:]:
        print(line)
except Exception as e:
    print(f"Error fetching logs: {e}")

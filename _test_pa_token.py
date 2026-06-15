#!/usr/bin/env python3
"""Test PA API tokens"""
import urllib.request, json

tokens = [
    ('from MEMORY.md', '34fe3a4cafefe3a4ac8d592119d5480a0b988971'),
    ('from .env', '1181b0064725fc1bb9f3043c19f943780eeebd3b'),
]

for label, token in tokens:
    url = 'https://www.pythonanywhere.com/api/v0/user/JHFGUF/files/path'
    req = urllib.request.Request(url, headers={'Authorization': 'Token ' + token})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        print(f'Token {label}: ✅ Valid!')
        print(f'  Files path: {data.get("files_path", "N/A")}')
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'Token {label}: ❌ {e.code} — {body[:100]}')

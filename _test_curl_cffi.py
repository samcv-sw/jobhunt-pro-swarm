"""Test curl_cffi against ALL job sources"""
from curl_cffi import requests
import json

# Test Indeed RSS with Chrome 120 TLS fingerprint
print("=== INDEED ===")
try:
    r = requests.get(
        "https://www.indeed.com/rss?q=network+engineer&l=Dubai&sort=date",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        impersonate="chrome120",
        timeout=15
    )
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
    items = r.text.count("<item>")
    print(f"Job <item> tags: {items}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== BAYT ===")
try:
    r = requests.get(
        "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        impersonate="chrome120",
        timeout=15
    )
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
    if r.status_code == 200:
        import re
        jobs = re.findall(r'"@type":"JobPosting"', r.text)
        titles = re.findall(r'<h[23][^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h', r.text, re.DOTALL)
        print(f"JSON-LD JobPostings: {len(jobs)}, Title matches: {len(titles)}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== DICE ===")
try:
    r = requests.get(
        "https://www.dice.com/jobs?q=network+engineer",
        impersonate="chrome120",
        timeout=15
    )
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"ERROR: {e}")

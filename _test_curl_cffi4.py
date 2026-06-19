"""Find Bayt API/JSON endpoint & fix Dice parser"""
from curl_cffi import requests
import re, json

print("=== BAYT API ENDPOINTS ===")
endpoints = [
    "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/",
    "https://www.bayt.com/api/jobs/search?country=uae&keyword=network+engineer",
    "https://www.bayt.com/en/uae/jobs/network-engineer-jobs/?format=json",
    "https://www.bayt.com/api/jobs/search/?country=uae&keyword=network+engineer",
]
for ep in endpoints:
    try:
        r = requests.get(ep, impersonate="chrome120", timeout=10, headers={"Accept": "application/json"})
        print(f"\n{ep}\n  Status: {r.status_code}, Type: {r.headers.get('content-type','?')[:50]}, Len: {len(r.text)}")
        if 'json' in r.headers.get('content-type',''):
            j = r.json()
            print(f"  Keys: {list(j.keys())[:10] if isinstance(j, dict) else f'array of {len(j)}'}")
    except Exception as e:
        print(f"\n{ep}\n  ERROR: {str(e)[:100]}")

print("\n\n=== DICE - search for job links ===")
r = requests.get("https://www.dice.com/jobs?q=network+engineer", impersonate="chrome120", timeout=15)
# Find card links
cards = re.findall(r'<a[^>]*data-testid="job-search-job-card-link"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r.text)
print(f"Card links: {len(cards)}")
for href, title in cards[:5]:
    clean = re.sub(r'<[^>]+>', '', title).strip()
    print(f"  {clean[:80]} → {href}")

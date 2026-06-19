"""Test Bayt.com WITHOUT cloudscraper (just httpx) to see if standard HTTP works"""
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

for url in [
    "https://www.bayt.com/en/international/jobs/network-jobs/",
    "https://www.bayt.com/en/uae/jobs/network-jobs/",
    "https://www.bayt.com/en/saudi-arabia/jobs/network-jobs/",
]:
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"{url[:50]:50s} | HTTP {resp.status_code}, {len(resp.text):>6} bytes | {'OK' if resp.status_code==200 else 'BLOCKED'}")
    except Exception as e:
        print(f"{url[:50]:50s} | ERROR: {e}")

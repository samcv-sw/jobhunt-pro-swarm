"""Check Dice.com response - can we extract actual job listings?"""
import requests, re, json

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})

# Test Dice search
print("=== Dice.com: Network Engineer in Dubai ===")
url = "https://www.dice.com/jobs?q=network+engineer&location=Dubai,%20United%20Arab%20Emirates"
r = session.get(url, timeout=30)
print(f"Status: {r.status_code}")
print(f"Length: {len(r.text)} chars")
text_lower = r.text.lower()

# Check content
keywords_found = {kw: kw in text_lower for kw in [
    "network engineer", "job", "position", "dubai", "apply", "salary",
    "jobcard", "searchresult", "job-listing", "job-card"
]}
print(f"Keywords found: {json.dumps(keywords_found, indent=2)}")

# Look for JSON data in page (Dice loads jobs via JS/API)
import re
json_patterns = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', r.text, re.DOTALL)
if json_patterns:
    print(f"\nFound __INITIAL_STATE__ JSON ({len(json_patterns[0])} chars)")
else:
    print("\nNo __INITIAL_STATE__ found")

# Check for inline job data
job_patts = re.findall(r'window\.__INITIAL_PROPS__\s*=\s*({.*?});', r.text, re.DOTALL)
if job_patts:
    print(f"Found __INITIAL_PROPS__ JSON ({len(job_patts[0])} chars)")

# Look for script tags with JSON
script_tag = re.findall(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if script_tag:
    print(f"Found __NEXT_DATA__ JSON ({len(script_tag[0])} chars)")

# Check if Dice API endpoint works directly
print("\n=== Dice API test ===")
api_url = "https://www.dice.com/api/v1/jobs/search?q=network+engineer&location=Dubai&page=1&pageSize=20"
r2 = session.get(api_url, timeout=30, headers={
    "Accept": "application/json",
    "Referer": "https://www.dice.com/jobs",
    "x-api-key": "1"
})
print(f"API Status: {r2.status_code}")
print(f"API Response: {r2.text[:300]}")

# Save full HTML
with open("proxy_test_results/dice_full_response.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print(f"\nFull HTML saved to: proxy_test_results/dice_full_response.html")

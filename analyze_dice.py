"""Analyze Dice.com HTML for job data extraction potential."""
import json, re

with open("proxy_test_results/dice_full_response.html", "r", encoding="utf-8") as f:
    html = f.read()

# Check for __NEXT_DATA__
next_data = re.findall(
    r'<script id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>',
    html, re.DOTALL
)
if next_data:
    d = json.loads(next_data[0])
    print(f"__NEXT_DATA__ found: {len(json.dumps(d))} chars")
    s = json.dumps(d, ensure_ascii=False)
    
    title_matches = re.findall(r'"jobTitle"[^:]*:\s*"([^"]+)"', s)
    company_matches = re.findall(r'"companyName"[^:]*:\s*"([^"]+)"', s)
    location_matches = re.findall(r'"location"[^:]*:\s*"([^"]+)"', s)
    
    print(f"Job titles found: {len(set(title_matches))}")
    print(f"Companies found: {len(set(company_matches))}")
    print(f"Locations found: {len(set(location_matches))}")
    
    if title_matches:
        print(f"\nSample job titles:")
        for t in list(set(title_matches))[:10]:
            print(f"  - {t}")
    if company_matches:
        print(f"\nSample companies:")
        for c in list(set(company_matches))[:5]:
            print(f"  - {c}")
    if location_matches:
        print(f"\nSample locations:")
        for loc in list(set(location_matches))[:5]:
            print(f"  - {loc}")
else:
    print("No __NEXT_DATA__ found")

# Find API endpoints
api_calls = re.findall(r'/api/v[12]/[a-z]+', html)
print(f"\nAPI endpoints: {list(set(api_calls))}")

# Search for jobId pattern
job_ids = re.findall(r'"jobId"\s*:\s*"([^"]+)"', html)
print(f"jobId instances: {len(set(job_ids))}")

# Check for Dice API endpoint pattern
search_apis = re.findall(r'(/api/v[^"\']*search[^"\']*)', html, re.IGNORECASE)
print(f"Search API endpoints: {list(set(search_apis))}")

import urllib.request, json

url = "https://jhfguf.pythonanywhere.com/api/v2/cloud-tick"
data = json.dumps({"action": "cloud_tick", "company_limit": 5}).encode()
headers = {"Content-Type": "application/json"}

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
resp = urllib.request.urlopen(req, timeout=240)
result = json.loads(resp.read())

print(f"Status: {result['status']}")
print(f"Campaigns: {result['campaigns_processed']}")
print(f"Emails: {result['emails_sent']}")
print(f"Errors: {result['errors']}")
print(f"Elapsed: {result.get('elapsed_sec', 'N/A')}s")

all_companies = []
for tenant_id, tenant in result.get("tenants", {}).items():
    for camp in tenant.get("campaigns", []):
        cid = camp["campaign_id"][:20]
        companies = [c["company"] for c in camp["result"].get("companies", [])]
        all_companies.extend(companies)
        statuses = [c["status"] for c in camp["result"].get("companies", [])]
        print(f"  {cid}: {len(companies)} companies: {companies}")
        print(f"    Statuses: {statuses}")

# Check for duplicates
unique = set(all_companies)
if len(all_companies) != len(unique):
    from collections import Counter
    dupes = {c: n for c, n in Counter(all_companies).items() if n > 1}
    print(f"\n⚠️  DUPLICATES FOUND: {dupes}")
else:
    print(f"\n✅ NO DUPLICATES: {len(unique)} unique companies across all campaigns")

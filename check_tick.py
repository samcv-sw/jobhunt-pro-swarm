import urllib.request, json, time

url = "https://jhfguf.pythonanywhere.com/api/v2/cloud-tick"
data = json.dumps({"action": "cloud_tick", "company_limit": 3}).encode()
headers = {"Content-Type": "application/json"}

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
resp = urllib.request.urlopen(req, timeout=240)
result = json.loads(resp.read())

print(f"Status: {result['status']}")
print(f"Campaigns: {result['campaigns_processed']}")
print(f"Emails: {result['emails_sent']}")
print(f"Errors: {result['errors']}")
print(f"Elapsed: {result.get('elapsed_sec', 'N/A')}s")

for tenant_id, tenant in result.get("tenants", {}).items():
    print(f"\n  Tenant: {tenant_id}")
    print(f"  Sent: {tenant.get('total_sent', 0)}")
    print(f"  Failed: {tenant.get('total_failed', 0)}")
    for camp in tenant.get("campaigns", []):
        cid = camp["campaign_id"][:20]
        res = camp["result"]
        companies = [c["company"] for c in res.get("companies", [])]
        print(f"    Campaign {cid}: {len(companies)} companies: {companies}")

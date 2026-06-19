# encoding: utf-8
"""Extract Bayt and Dice jobs properly"""
from curl_cffi import requests
import re

print("=== DICE FULL PARSE ===")
r = requests.get("https://www.dice.com/jobs?q=network+engineer", impersonate="chrome120", timeout=15)
cards = re.findall(r'<a[^>]*data-testid="job-search-job-card-link"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r.text)
print(f"Found {len(cards)} job cards:")
for href, title_html in cards[:10]:
    clean = re.sub(r'<[^>]+>', '', title_html).strip()
    # Parse company from href or nearby
    company = "Unknown"
    if "/company/" in href:
        company = href.split("/company/")[1].split("/")[0].replace("-", " ").title()
    print(f"  {clean[:60]} | {company}")

print("\n=== BAYT FULL PARSE ===")
r = requests.get("https://www.bayt.com/en/uae/jobs/network-engineer-jobs/", impersonate="chrome120", timeout=15)
html = r.text

# Find job cards: <h2> with link inside
job_sections = re.findall(r'<h2[^>]*><a[^>]*href="(/en/[^"]*/jobs/[^"]*)"[^>]*>(.*?)</a></h2>', html)
print(f"H2 job links: {len(job_sections)}")
for href, title_html in job_sections[:5]:
    clean = re.sub(r'<[^>]+>', '', title_html).strip()
    print(f"  {clean[:80]} | https://www.bayt.com{href}")

# Find company names 
companies = re.findall(r'<a[^>]*href="(/en/[^/]+/)"[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</a>', html)
print(f"\nCompany links: {len(companies)}")
for href, name in companies[:5]:
    print(f"  {name.strip()[:40]} | {href}")

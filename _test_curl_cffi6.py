# encoding: utf-8
"""Save HTML snippets to inspect structure"""
from curl_cffi import requests

# Dice - get a card's HTML
r = requests.get("https://www.dice.com/jobs?q=network+engineer", impersonate="chrome120", timeout=15)
# Find position of first card link
idx = r.text.find('data-testid="job-search-job-card-link"')
print("=== DICE first card HTML (500 chars) ===")
print(r.text[idx:idx+800])

print("\n\n=== BAYT first few search result HTML (1000 chars) ===")
r2 = requests.get("https://www.bayt.com/en/uae/jobs/network-engineer-jobs/", impersonate="chrome120", timeout=15)
# Find position of first job URL from JSON-LD
idx2 = r2.text.find('/en/uae/jobs/')
print(r2.text[idx2:idx2+1000])

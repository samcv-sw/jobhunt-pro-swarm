import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json

base_url = "https://jhfguf.pythonanywhere.com"
visited = set()
to_visit = [base_url]
results = {"200": [], "404": [], "500": [], "other": []}
forms_found = []

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
})

while to_visit and len(visited) < 300: # safety limit
    current_url = to_visit.pop(0)
    if current_url in visited:
        continue
    visited.add(current_url)

    try:
        response = session.get(current_url, timeout=10)
        status = response.status_code
        if status == 200:
            results["200"].append(current_url)
        elif status == 404:
            results["404"].append(current_url)
        elif status >= 500:
            results["500"].append(current_url)
        else:
            results["other"].append({"url": current_url, "status": status})

        if status == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(base_url, href)
                parsed_full = urlparse(full_url)
                
                if parsed_full.netloc == urlparse(base_url).netloc:
                    clean_url = full_url.split('#')[0]
                    if clean_url not in visited and clean_url not in to_visit and "/login" not in clean_url and "/register" not in clean_url and "/logout" not in clean_url and "/dashboard" not in clean_url and "/admin" not in clean_url:
                        to_visit.append(clean_url)
            
            for form in soup.find_all('form', action=True):
                forms_found.append({"page": current_url, "action": form['action'], "method": form.get('method', 'GET').upper()})

    except Exception as e:
        results["500"].append(current_url + f" (Error: {str(e)})")

    time.sleep(0.05)

with open("qa_report.json", "w") as f:
    json.dump({"visited": len(visited), "status_codes": results, "forms": forms_found}, f, indent=4)

print(f"Crawl finished. Visited {len(visited)} URLs. 404s: {len(results['404'])}, 500s: {len(results['500'])}")

"""
job_collector.py — Local scraper for Indeed + Bayt + NaukriGulf
Runs on Sam's PC (local IP = no 403s). Pushes jobs to PA.

Usage: python3 job_collector.py

Schedule: Windows Task Scheduler every 4h
"""

import requests, json, time, os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# ── CONFIG ──
PA_API = "https://jhfguf.pythonanywhere.com/api/jobs/bulk_import"
TOKEN = "874997673d6b9787dc4e3a938dd45a1930f1c85c"
LOG_FILE = os.path.join(os.path.dirname(__file__), "_collector_log.json")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
COUNTRIES = {
    "UAE": ["Dubai", "Abu Dhabi", "Sharjah"],
    "Saudi": ["Riyadh", "Jeddah", "Khobar"],
    "Qatar": ["Doha"],
    "Kuwait": ["Kuwait City"],
    "Lebanon": ["Beirut"],
}

def fetch_indeed(query, location, limit=15):
    """Scrape Indeed.com search results"""
    url = f"https://www.indeed.com/jobs?q={quote_plus(query)}&l={quote_plus(location)}&sort=date&limit={limit}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    if r.status_code != 200:
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for card in soup.select("[data-jk]") or soup.select("a[href*=viewjob]"):
        jk = card.get("data-jk", "")
        title = card.select_one(".jobTitle") or card.select_one("h2")
        company = card.select_one(".companyName") or card.select_one("[data-company-name]")
        
        if jk:
            jobs.append({
                "title": title.get_text(strip=True)[:100] if title else query,
                "company": company.get_text(strip=True)[:80] if company else "",
                "location": location,
                "url": f"https://www.indeed.com/viewjob?jk={jk}",
                "source": "indeed",
                "country": location,
            })
    return jobs[:limit]

def fetch_bayt(query, location, limit=15):
    """Scrape Bayt.com search results"""
    url = f"https://www.bayt.com/en/international/jobs/{quote_plus(query.replace(' ','-'))}-jobs-in-{quote_plus(location.replace(' ','-'))}/"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    if r.status_code != 200:
        return []
    
    jobs = []
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("li.has-pointer-d") or soup.select("article")
    for card in cards[:limit]:
        title = card.select_one(".jb_title h2 a") or card.select_one("h2")
        company = card.select_one(".jb_company a") or card.select_one(".jb_company")
        if title:
            jobs.append({
                "title": title.get_text(strip=True)[:100],
                "company": company.get_text(strip=True)[:80] if company else "",
                "location": location,
                "url": "https://www.bayt.com" + (title.get("href", "") if hasattr(title, "get") else ""),
                "source": "bayt",
                "country": location,
            })
    return jobs[:limit]

def push_to_pa(jobs, log_file):
    """Send collected jobs to PythonAnywhere"""
    if not jobs:
        return 0
    
    # Dedup by URL
    seen = set()
    unique = []
    for j in jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
    
    # Push batch
    r = requests.post(PA_API, headers={"Authorization": f"Token {TOKEN}"},
                      json={"jobs": unique}, timeout=30)
    
    if r.status_code == 200:
        result = r.json()
        print(f"  PA: {result.get('imported', 0)} imported, {result.get('skipped', 0)} skipped")
    else:
        print(f"  PA error: HTTP {r.status_code}")
    
    # Log
    log = {"ts": time.time(), "pushed": len(unique), "status": r.status_code}
    with open(log_file, "w") as f:
        json.dump(log, f)
    
    return len(unique)

def main():
    queries = ["network engineer", "network administrator", "it support engineer", "system administrator"]
    all_jobs = []
    
    for country, cities in COUNTRIES.items():
        for city in cities:
            for query in queries:
                print(f"  Indeed: {query} in {city}...")
                jobs = fetch_indeed(query, city)
                print(f"    → {len(jobs)} jobs")
                all_jobs.extend(jobs)
                time.sleep(0.5)
    
    print(f"\nTotal collected: {len(all_jobs)}")
    pushed = push_to_pa(all_jobs, LOG_FILE)
    print(f"Pushed to PA: {pushed}")

if __name__ == "__main__":
    main()

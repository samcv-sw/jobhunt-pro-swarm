import httpx, re, json, time
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup

# DuckDuckGo HTML search for jobs from MULTIPLE sources
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
h = {"User-Agent": ua}

results = {}
queries = [
    ("network engineer", "Dubai"),
    ("network engineer", "Abu Dhabi"),
    ("network engineer", "Riyadh"),
    ("network engineer", "Beirut"),
    ("network engineer", "Doha"),
    ("network engineer", "Kuwait"),
]

print("=== DUCKDUCKGO: Multi-source job search ===\n")
for title, city in queries:
    q = f"{title} jobs in {city} - apply - submit"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"
    
    with httpx.Client(headers=h, follow_redirects=True, timeout=15) as c:
        r = c.get(url)
    
    if r.status_code != 200:
        print(f"  {city}: HTTP {r.status_code}")
        time.sleep(1)
        continue
    
    soup = BeautifulSoup(r.text, "html.parser")
    job_links = []
    
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        if href.startswith("//"):
            href = "https:" + href
        
        # Extract actual URL from DuckDuckGo redirect
        actual_url = href
        if "uddg=" in href:
            actual_url = parse_qs(urlparse(href).query).get("uddg", [href])[0]
        
        text = a.text.strip()
        
        # Classify source
        source = "other"
        if "linkedin.com" in actual_url:
            source = "linkedin"
        elif "indeed.com" in actual_url:
            source = "indeed"
        elif "naukrigulf.com" in actual_url:
            source = "naukrigulf"
        elif "bayt.com" in actual_url:
            source = "bayt"
        elif "gulftalent.com" in actual_url:
            source = "gulftalent"
        
        job_links.append({"source": source, "title": text[:60], "url": actual_url[:100]})
    
    results[f"{city}"] = len(job_links)
    
    print(f"\n  {title} in {city}:")
    print(f"    Total results: {len(job_links)}")
    
    # Count by source
    sources = {}
    for jl in job_links:
        src = jl["source"]
        sources[src] = sources.get(src, 0) + 1
    
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src + ':':15s} {count}")
    
    if job_links:
        print("    Top results:")
        for jl in job_links[:3]:
            print(f"      [{jl['source'][:8]:8s}] {jl['title'][:50]}")

    time.sleep(1.5)  # polite delay

print(f"\n\n=== SUMMARY ===")
for city, count in results.items():
    print(f"  {city:15s}: {count} results")

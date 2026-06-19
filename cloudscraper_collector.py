"""
CLOUDSCRAPER COLLECTOR v1 — Bayt-focused, bypasses Cloudflare, uploads to PA
Replaces nodriver_collector.py for headless/cron environments
"""
import cloudscraper, re, json, os, time
from datetime import datetime

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nodriver_jobs.json")
PA_API = "https://jhfguf.pythonanywhere.com/api/nodriver-feed"

TITLES = ["network engineer", "network administrator", "network technician", 
          "it support engineer", "system administrator", "network security engineer",
          "devops engineer", "it manager", "technical support engineer", "noc engineer"]

COUNTRIES = [("uae", "UAE"), ("saudi-arabia", "Saudi Arabia"), ("qatar", "Qatar"), ("kuwait", "Kuwait"), ("lebanon", "Lebanon"), ("bahrain", "Bahrain"), ("oman", "Oman")]

# Cloudflare-excluded terms (job types that aren't what we want)
EXCLUDE = ["search", "network-engineer", "it-support", "system-admin", "network-security", 
           "engineering", "root", "healthcare", "transport", "science", "designer", 
           "skilled", "personal-service"]

def scrape_bayt(scraper, title, country_code, country_name):
    jobs = []
    slug = title.replace(' ', '-')
    url = f"https://www.bayt.com/en/{country_code}/jobs/{slug}-jobs/"
    try:
        resp = scraper.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"  Bayt [{title[:30]}/{country_code}]: HTTP {resp.status_code}", flush=True)
            return jobs
        
        html = resp.text
        
        # Build exclude pattern
        exclude_pattern = '|'.join(EXCLUDE)
        h2s = re.findall(
            rf'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/(?!{exclude_pattern})[^"]+)"[^>]*>(.*?)</a>.*?</h2>',
            html, re.DOTALL
        )
        
        for href, title_html in h2s:
            title_t = re.sub(r'<[^>]+>', '', title_html).strip()
            title_t = title_t.replace('&amp;', '&').replace('&#39;', "'")
            if len(title_t) > 5 and 'jobs in' not in title_t.lower():
                jobs.append({
                    'title': title_t,
                    'company': 'Unknown',
                    'url': f"https://www.bayt.com{href}",
                    'source': 'bayt',
                    'location': country_name
                })
        print(f"  Bayt [{title[:30]}/{country_code}]: {len(jobs)} jobs", flush=True)
    except Exception as e:
        print(f"  Bayt [{title}/{country_code}]: ERROR - {str(e)[:80]}", flush=True)
    return jobs

def main():
    t_start = datetime.now()
    print(f">>> CLOUDSCRAPER BAYT COLLECTOR - {t_start.strftime('%H:%M:%S')}", flush=True)
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False, 'desktop': True}
    )
    
    all_jobs = []
    total_queries = 0
    
    for title in TITLES:
        for country_code, country_name in COUNTRIES:
            total_queries += 1
            jobs = scrape_bayt(scraper, title, country_code, country_name)
            all_jobs.extend(jobs)
            time.sleep(1.5)  # Rate limiting
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for j in all_jobs:
        if j['url'] and j['url'] not in seen:
            seen.add(j['url'])
            unique.append(j)
    
    elapsed = (datetime.now() - t_start).total_seconds()
    
    print(f"\n>>> DONE in {elapsed:.0f}s: {len(all_jobs)} total -> {len(unique)} unique from {total_queries} queries", flush=True)
    
    # Save locally
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'collected_at': datetime.now().isoformat(),
            'total': len(unique),
            'elapsed_seconds': elapsed,
            'jobs': unique
        }, f, indent=2, ensure_ascii=False)
    print(f">>> Saved to {OUTPUT_FILE}", flush=True)
    
    # Upload to PA
    try:
        import requests as req
        r = req.post(PA_API, json={'jobs': unique}, timeout=30)
        print(f">>> PA upload: {r.status_code} - {r.text[:200]}", flush=True)
    except Exception as e:
        print(f">>> PA upload failed: {e}", flush=True)
    
    return unique

if __name__ == "__main__":
    main()

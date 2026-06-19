"""
Debug — check if original regex patterns work with cloudscraper HTML
"""
import cloudscraper, re, json

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False, 'desktop': True}
)

TITLES = ["network engineer", "network administrator", "network technician", 
          "it support engineer", "system administrator", "network security engineer",
          "devops engineer", "it manager", "technical support engineer", "noc engineer"]

COUNTRIES = [("uae", "UAE"), ("saudi-arabia", "Saudi Arabia"), ("qatar", "Qatar"), ("kuwait", "Kuwait"), ("lebanon", "Lebanon"), ("bahrain", "Bahrain"), ("oman", "Oman")]

# Test one query first
slug = TITLES[0].replace(' ', '-')
country_code, country_name = COUNTRIES[0]
url = f"https://www.bayt.com/en/{country_code}/jobs/{slug}-jobs/"

resp = scraper.get(url, timeout=30)
html = resp.text

# Original regex
h2s = re.findall(r'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/(?!search|network-engineer|it-support|system-admin|network-security|engineering|root|healthcare|transport|science|designer|skilled|personal-service)[^"]+)"[^>]*>(.*?)</a>.*?</h2>', html, re.DOTALL)
print(f"Original regex found: {len(h2s)} matches", flush=True)

# Simpler regex
h2s2 = re.findall(r'<h2[^>]*>.*?<a[^>]*href="(/en/[^/]+/jobs/[^"]+)"[^>]*>(.*?)</a>.*?</h2>', html, re.DOTALL)
print(f"Simple regex found: {len(h2s2)} matches", flush=True)

# Sample the matches
for href, title_html in h2s2[:5]:
    title_t = re.sub(r'<[^>]+>', '', title_html).strip().replace('&amp;', '&').replace('&#39;', "'")
    print(f"  [{title_t[:50]}] -> {href[:50]}", flush=True)

# Check for job cards with company name
company_matches = re.findall(r'<a[^>]*class="[^"]*job-title[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
print(f"\n'job-title' link pattern: {len(company_matches)}", flush=True)

# Check for company names
company_divs = re.findall(r'class="[^"]*company-name[^"]*"[^>]*>(.*?)<', html, re.DOTALL)
print(f"'company-name' divs: {len(company_divs)}", flush=True)
for c in company_divs[:3]:
    print(f"  Company: {c.strip()[:50]}", flush=True)

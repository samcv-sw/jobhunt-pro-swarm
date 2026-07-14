# Milestone 7 Scraper Expansion Investigation Report

## 1. Observation

### Existing Scraper Codebase Locations
The scraper implementations are located in two primary core files:
1. **`core/multi_source_scraper.py`**:
   - `BaseScraper` definition (line 184):
     ```python
     class BaseScraper:
         """Abstract base class for all job scrapers."""
         source_name: str = "base"
         ...
     ```
   - Platform scrapers: `BaytScraper` (line 299), `NaukriScraper` (line 393), `WuzzufScraper` (line 499), `IndeedScraper` (line 576), `GoogleJobsScraper` (line 730), `LinkedInScraper` (line 879), `GlassdoorScraper` (line 968), `WellfoundScraper` (line 1040), `DiceScraper` (line 1066), `SeekScraper` (line 1096), `StepStoneScraper` (line 1123), `WWRScraper` (line 1152), `ZipRecruiterScraper` (line 1178), `XingScraper` (line 1220), `NaukriIndiaScraper` (line 1255), `JoobleScraper` (line 1293), and `UpworkScraper` (line 1334).
2. **`core/pa_job_scraper.py`**:
   - Contains unified/rotating scraping tasks with free integrations: hh.ru (line 567), Indeed RSS (line 813), Glassdoor Free (line 870), LinkedIn XHR (line 1011), Remotive API (line 1308), Arbeitnow API (line 1352), RemoteOK API (line 1427), WeWorkRemotely RSS (line 1490), The Muse API (line 1570), and Jobicy API (line 1627).

### Scraper Registration & Execution Setup
- **`core/matrix_scrape_handler.py`**:
   - Maps scraper names to classes in `SCRAPER_MAP` (line 46).
   - Monkey-patches `BaseScraper._get` (line 75) to route requests via the Cloudflare Worker scrape proxy (`WORKER_URL = "https://jobhunt-pro-router.samsalameh-cv.workers.dev"`), falling back to `curl_cffi` TLS impersonation if the worker proxy fails or returns Cloudflare blocks.
- **`scripts/run_all_scrapers.py`**:
   - Executes the scraping pool concurrently (line 12):
     ```python
     PLATFORMS = [
         "linkedin", "indeed", "bayt", "glassdoor", "wuzzuf",
         "naukrigulf", "dice", "seek", "stepstone", "wwr",
         "wellfound", "ziprecruiter", "xing", "naukriindia",
         "jooble", "upwork"
     ]
     ```

### Code Reference Points for Expansion
- **`core/multi_platform_apply.py`** already contains an asynchronous `GulftalentScraper` class (line 1235) with CSS card selectors (`div.module.job, div[class*='job']:not([class*='header']), li[class*='job']`).
- **`core/pa_job_scraper.py`** contains methods for public APIs: `search_remotive` (line 1308) and `search_remoteok` (line 1427).

---

## 2. Logic Chain

1. **Scraper Pool Expansion Pattern**: Any scraper integrated into the GHA (GitHub Actions) concurrent scraper pipeline must have a class subclassing `BaseScraper` in `core/multi_source_scraper.py`. It must be mapped in `core/matrix_scrape_handler.py:SCRAPER_MAP` and added to `scripts/run_all_scrapers.py:PLATFORMS`.
2. **Proxy Bypass Mechanism**: `core/matrix_scrape_handler.py`'s `monkey_patch_scraper` redirects all requests made via `BaseScraper._get` through the Cloudflare Worker. This allows new scrapers targeting highly protected sites like GulfTalent to bypass bot verification screens without writing custom bypass handlers locally.
3. **Drafting classes**:
   - **GulfTalent**: Adapt `GulftalentScraper` from `core/multi_platform_apply.py` into a synchronous scraper class leveraging `BaseScraper._get` and BeautifulSoup.
   - **Remotive & RemoteOK**: Adapt the public API search implementations from `core/pa_job_scraper.py` into synchronous `BaseScraper` subclasses in `core/multi_source_scraper.py` that query their respective free endpoints.

---

## 3. Caveats

- **CODE_ONLY Network Mode**: No external HTTP requests could be sent to test real-time connectivity to GulfTalent, Remotive, or RemoteOK endpoints. Implementation is based entirely on existing codebase structures and documented URL configurations.
- **GulfTalent Cloudflare challenges**: Even though the Worker routing is active, if the proxy IP gets blocked, requests will fall back to `curl_cffi` which may fail depending on the host's networking environment.

---

## 4. Conclusion

We recommend adding the following three scrapers to the active scraper matrix pool:

### Proposed Code Integrations (to be added to `core/multi_source_scraper.py`)

#### 1. `GulftalentScraper`
```python
class GulftalentScraper(BaseScraper):
    """Scraper for GulfTalent.com - GCC focused job board."""
    source_name = "gulftalent"

    def search(self, query: str, location: str = "", limit: int = 15) -> list[dict]:
        jobs = []
        try:
            q = quote_plus(query)
            url = f"https://www.gulftalent.com/jobs?q={q}"
            if location:
                url += f"&l={quote_plus(location)}"

            resp = self._get(url, extra_headers={"Referer": "https://www.gulftalent.com/"})
            if not resp or resp.status_code != 200:
                return jobs

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(
                "div.module.job, div[class*='job']:not([class*='header']), li[class*='job'], div.search-result"
            )

            for card in cards[:limit]:
                title_el = card.select_one("h2 a, a[class*='title'], h3 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.gulftalent.com{href}"

                company_el = card.select_one("span[class*='company'], .company, a[class*='company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                loc_el = card.select_one("span[class*='location'], .location, span[class*='loc']")
                loc = loc_el.get_text(strip=True) if loc_el else location or "Remote"

                desc_el = card.select_one("p.job-description, .snippet, div.description")
                snippet = desc_el.get_text(strip=True)[:300] if desc_el else ""

                jobs.append(self._build_job_dict(title, company, loc, href, snippet))
        except Exception as e:
            logger.debug(f"GulftalentScraper error: {e}")
        return jobs
```

#### 2. `RemotiveScraper`
```python
class RemotiveScraper(BaseScraper):
    """Scraper for Remotive.com API - Remote jobs."""
    source_name = "remotive"

    def search(self, query: str, location: str = "", limit: int = 15) -> list[dict]:
        jobs = []
        try:
            q = quote_plus(query)
            url = f"https://remotive.com/api/remote-jobs?search={q}&limit={limit}"
            resp = self._get(url)
            if not resp or resp.status_code != 200:
                return jobs

            data = resp.json()
            for j in data.get("jobs", []):
                title = j.get("title", "")
                company = j.get("company_name", "")
                href = j.get("url", "")
                loc = j.get("candidate_required_location", "Remote")
                desc_html = j.get("description", "")
                snippet = BeautifulSoup(desc_html, "html.parser").get_text(strip=True)[:300] if desc_html else ""
                salary = j.get("salary", "")
                
                jobs.append(self._build_job_dict(title, company, loc, href, snippet, salary=salary))
                if len(jobs) >= limit:
                    break
        except Exception as e:
            logger.debug(f"RemotiveScraper error: {e}")
        return jobs
```

#### 3. `RemoteOKScraper`
```python
class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK.com API - Tech-focused Remote jobs."""
    source_name = "remoteok"

    def search(self, query: str, location: str = "", limit: int = 15) -> list[dict]:
        jobs = []
        try:
            url = "https://remoteok.com/api"
            resp = self._get(url, extra_headers={"User-Agent": "Mozilla/5.0"})
            if not resp or resp.status_code != 200:
                return jobs

            data = resp.json()
            kw = query.lower().split()
            for item in data:
                if not isinstance(item, dict) or not item.get("position"):
                    continue
                title = item.get("position", "")
                company = item.get("company", "")
                href = item.get("url", "")
                tags = " ".join(item.get("tags") or []).lower()
                
                tl = title.lower()
                if kw and not any(k in tl or k in tags for k in kw):
                    continue
                
                desc_html = item.get("description", "")
                snippet = BeautifulSoup(desc_html, "html.parser").get_text(strip=True)[:300] if desc_html else ""
                salary = item.get("salary", "")
                
                jobs.append(self._build_job_dict(title, company, "Remote", href, snippet, salary=salary))
                if len(jobs) >= limit:
                    break
        except Exception as e:
            logger.debug(f"RemoteOKScraper error: {e}")
        return jobs
```

### Handler Maps Updates
Add the new classes to `core/matrix_scrape_handler.py`:
```python
from core.multi_source_scraper import (
    # ... existing ...
    GulftalentScraper,
    RemotiveScraper,
    RemoteOKScraper,
)

SCRAPER_MAP = {
    # ... existing ...
    "gulftalent": GulftalentScraper,
    "remotive": RemotiveScraper,
    "remoteok": RemoteOKScraper,
}
```

Add the platforms to `scripts/run_all_scrapers.py`:
```python
PLATFORMS = [
    # ... existing ...
    "gulftalent", "remotive", "remoteok"
]
```

---

## 5. Verification Method

### Testing the new scrapers locally:
Create a temporary script `test_expanded_scrapers.py` and run it via Python:
```python
import sys
sys.path.insert(0, '.')
from core.multi_source_scraper import GulftalentScraper, RemotiveScraper, RemoteOKScraper

def test_run():
    scrapers = [
        GulftalentScraper(),
        RemotiveScraper(),
        RemoteOKScraper(),
    ]
    for s in scrapers:
        print(f"Testing Scraper: {s.source_name}...")
        jobs = s.search("network engineer", "Dubai", limit=3)
        print(f"Found {len(jobs)} jobs.")
        for j in jobs:
            print(f" - {j['title']} at {j['company']} ({j['location']})")

if __name__ == '__main__':
    test_run()
```
Run `python test_expanded_scrapers.py` to confirm they successfully parse and format listings without raising syntax or runtime exceptions.

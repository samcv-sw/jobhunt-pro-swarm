import asyncio
from core.multi_source_scraper import LinkedInScraper, IndeedScraper, BaytScraper, WuzzufScraper, NaukriScraper

def test_scrapers():
    query = "network engineer"
    location = "Dubai"
    limit = 2
    
    print("Testing LinkedIn...")
    try:
        li = LinkedInScraper().search(query, location, limit)
        print(f"LinkedIn found: {len(li)} jobs")
    except Exception as e:
        print(f"LinkedIn error: {e}")

    print("Testing Indeed...")
    try:
        ind = IndeedScraper().search(query, location, limit)
        print(f"Indeed found: {len(ind)} jobs")
    except Exception as e:
        print(f"Indeed error: {e}")

    print("Testing Bayt...")
    try:
        bayt = BaytScraper().search(query, location, limit)
        print(f"Bayt found: {len(bayt)} jobs")
    except Exception as e:
        print(f"Bayt error: {e}")

    print("Testing Naukri...")
    try:
        naukri = NaukriScraper().search(query, location, limit)
        print(f"Naukri found: {len(naukri)} jobs")
    except Exception as e:
        print(f"Naukri error: {e}")
        
    print("Testing Wuzzuf...")
    try:
        wuzzuf = WuzzufScraper().search(query, location, limit)
        print(f"Wuzzuf found: {len(wuzzuf)} jobs")
    except Exception as e:
        print(f"Wuzzuf error: {e}")

if __name__ == "__main__":
    test_scrapers()

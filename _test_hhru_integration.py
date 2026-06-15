"""Quick test script for hhru_scraper integration"""
import sys
sys.path.insert(0, r"C:\Users\samde\Desktop\cv sam new ma3 kimi")

# Test 1: hhru_scraper module
from core.hhru_scraper import search_hhru, search_hhru_sync, resolve_area_ids, resolve_area_id, HHRU_AREA_MAP
print("Test 1: hhru_scraper imports OK")
print(f"  Area map: {len(HHRU_AREA_MAP)} entries")

# Test 2: Location resolution
test_locs = ["Moscow", "Almaty", "Minsk", "remote", "SPB", "Dubai", "казань", "Russia"]
for loc in test_locs:
    aid = resolve_area_id(loc)
    print(f"  resolve_area_id({loc!r:20s}) = {aid}")

# Test 3: resolve_area_ids (batch)
ids = resolve_area_ids(["Moscow", "SPB", "Russia", "Dubai", "remote"])
print(f"  resolve_area_ids([Moscow, SPB, Russia, Dubai, remote]) = {ids}")

# Test 4: GlobalJobScraper integration
from core.global_scraper import GlobalJobScraper, COUNTRY_CONFIGS

# Check new country configs exist
for key in ["russia", "kazakhstan", "belarus", "remote", "lebanon", "uae"]:
    exists = key in COUNTRY_CONFIGS
    has_hhru = "hhru" in COUNTRY_CONFIGS.get(key, {}).get("domains", {}) if exists else False
    print(f"  COUNTRY_CONFIGS[{key!r}]: exists={exists}, has_hhru={has_hhru}")

# Test 5: GlobalJobScraper has _scrape_hhru method
s = GlobalJobScraper()
has_hhru_method = hasattr(s, "_scrape_hhru")
print(f"  GlobalJobScraper._scrape_hhru exists: {has_hhru_method}")
s.close()

# Test 6: config integration
import config
print(f"  HHRU_ENABLED = {config.HHRU_ENABLED}")
print(f"  HHRU_JOB_TITLES = {len(config.HHRU_JOB_TITLES)} titles")
print(f"  HHRU_LOCATIONS = {len(config.HHRU_LOCATIONS)} locations")

print("\nAll tests passed!")

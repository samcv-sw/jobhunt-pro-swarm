"""Check app.routes path collection for scrapers/health and webhook routes."""
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/jobhunt_test.db"
os.environ["TURSO_DATABASE_URL"] = ""

from backend.main import app  # noqa: E402

paths = [getattr(route, "path", "") for route in app.routes]
print("TOTAL ROUTES:", len(paths))
for p in paths:
    if "scraper" in p or "webhook" in p or "health" in p or "billing" in p or "payment" in p:
        print("MATCH:", repr(p))
print("scrapers/health present:", "/api/v1/scrapers/health" in paths)
print("any webhook:", [p for p in paths if "webhook" in p])
print("empty-string count:", sum(1 for p in paths if p == ""))

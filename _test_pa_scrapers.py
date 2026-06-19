"""Test Dice and Wuzzuf scrapers on PA via the app"""
import requests, json
h = {"Authorization": "Token 874997673d6b9787dc4e3a938dd45a1930f1c85c"}

# Hit the new /api/test-scrapers endpoint (create one if needed)
# For now, hit a debug endpoint that imports and runs the scrapers
r = requests.get("https://jhfguf.pythonanywhere.com/api/test/dice?q=network+engineer&l=dubai", timeout=30)
print(f"[Dice] HTTP {r.status_code}: {r.text[:500]}")

r = requests.get("https://jhfguf.pythonanywhere.com/api/test/wuzzuf?q=network+engineer&l=uae", timeout=30)
print(f"\n[Wuzzuf] HTTP {r.status_code}: {r.text[:500]}")

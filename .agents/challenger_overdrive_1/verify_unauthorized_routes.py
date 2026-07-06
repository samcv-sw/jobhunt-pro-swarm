import os
import sys
from fastapi.testclient import TestClient

# Set environment variables
os.environ["TESTING"] = "true"
# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.main import app
    print("Successfully imported FastAPI app.")
except Exception as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

client = TestClient(app)

routes_to_test = [
    # (path, method, payload)
    ("/api/v1/checkout", "POST", {"tier": "pro", "user_id": "test_user"}),
    ("/api/v1/scrape", "POST", {"user_id": "test_user", "target_urls": ["http://example.com"]}),
    ("/api/v1/generate-cover-letter", "POST", {"user_cv": "my cv", "job_description": "job description"}),
    ("/api/v1/ai/generate-cover-letter/stream", "POST", {"user_cv": "my cv", "job_description": "job description"}),
    ("/api/v1/accounts", "POST", {"tenant_id": "tenant-1", "currency": "CREDITS", "balance_cents": 100}),
]

print("Starting verification of unauthorized /api/v1/* routes...")
failures = []

for path, method, payload in routes_to_test:
    # 1. No Authorization header
    if method == "POST":
        response = client.post(path, json=payload)
    else:
        response = client.get(path)
    
    if response.status_code != 401:
        failures.append(f"Route {method} {path} returned {response.status_code} instead of 401 (no auth)")
    else:
        print(f"PASS: {method} {path} returned 401 (no auth)")
        
    # 2. Invalid Authorization header
    if method == "POST":
        response = client.post(path, json=payload, headers={"Authorization": "Bearer invalid_token_here"})
    else:
        response = client.get(path, headers={"Authorization": "Bearer invalid_token_here"})
        
    if response.status_code != 401:
        failures.append(f"Route {method} {path} returned {response.status_code} instead of 401 (invalid token)")
    else:
        print(f"PASS: {method} {path} returned 401 (invalid token)")

if failures:
    print("\nVerification failed! The following issues were found:")
    for failure in failures:
        print(f" - {failure}")
    sys.exit(1)
else:
    print("\nAll unauthorized checks successfully passed (all returned 401).")
    sys.exit(0)

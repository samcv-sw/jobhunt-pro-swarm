import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath('web'))
from app_v2 import app

client = TestClient(app)

# Login first
login_data = {"email": "test_ai_agent@samde.com", "password": "password123"}
response = client.post("/login", data=login_data)
print(f"Login status: {response.status_code}")

# Get dashboard
response = client.get("/user-dashboard")
print(f"Dashboard status: {response.status_code}")
with open("test_dashboard.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Saved test_dashboard.html")

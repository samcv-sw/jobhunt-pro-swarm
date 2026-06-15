import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath('web'))
from app_v2 import app, get_verified_user_id

app.dependency_overrides[get_verified_user_id] = lambda: 1

client = TestClient(app)
response = client.get("/user-dashboard")
with open("test_dashboard.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Saved test_dashboard.html")

import sys
sys.path.append('.')
from app_v2 import app
from fastapi.testclient import TestClient

client = TestClient(app)
# Mock user login by overriding the dependency or something
# Wait, user_dashboard needs a valid user from DB?
# I'll just write a mock endpoint that returns `_build_dashboard_shell`!

from app_v2 import _build_dashboard_shell
html = _build_dashboard_shell(
    user={"id": 1, "name": "Test User", "wallet_balance": 1500},
    user_id=1,
    content_html="<div style='background: blue; padding: 20px;'><h1>Main Content!</h1></div>",
    title="Dashboard",
    active_page="dashboard"
)
with open("test_shell.html", "w", encoding="utf-8") as f:
    f.write(html)

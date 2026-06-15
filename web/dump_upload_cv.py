import sys
import os
sys.path.append(os.path.abspath('.'))

from app_v2 import app, _build_dashboard_shell, render_template

user_mock = {
    "user_id": 1,
    "email": "test@example.com",
    "wallet_balance": 100.0,
    "full_name": "Test User"
}

html = render_template("upload_cv_v2.html", user=user_mock, user_id=1)
shell_html = _build_dashboard_shell(user_mock, 1, html, "Upload CV", "upload-cv")

with open("test_upload_cv.html", "w", encoding="utf-8") as f:
    f.write(shell_html)

print("Saved test_upload_cv.html")

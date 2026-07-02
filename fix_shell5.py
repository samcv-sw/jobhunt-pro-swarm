import os
import re

app_file = "web/app_v2.py"
with open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

# Update all calls to _build_dashboard_shell to pass request=request
# But first, ensure we aren't doubling up
if "request=request" not in content.split("_build_dashboard_shell", 2)[-1][:50]:
    content = re.sub(
        r'(_build_dashboard_shell\([^)]+?,\s*["\'][a-zA-Z0-9_-]+["\'])\)',
        r'\1, request=request)',
        content
    )
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed calls to _build_dashboard_shell")
else:
    print("Calls might already be fixed.")
